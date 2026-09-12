import json
from datetime import date
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier

from app.config import Config
from app.ml.features import load_feature_frame, latest_feature_rows, ALL_FEATURES
from app.repository import upsert_prediction, add_backtest_result


def _prepare_xy(frame: pd.DataFrame):
    data = frame.dropna(subset=["target"]).copy()
    data = data.dropna(subset=["ret_20", "ma_ratio_50", "volatility_20"]).copy()
    if data.empty:
        raise RuntimeError("No hay suficientes datos para entrenar. Cargue historicos de mercado primero.")

    feature_cols = [c for c in ALL_FEATURES if c in data.columns]
    X = data[feature_cols].replace([np.inf, -np.inf], np.nan)
    # XGBoost tolera NaN; se preservan para no inventar datos macro/fundamentales ausentes.
    y = data["target"].astype(int)
    return data, X, y, feature_cols


def train_model() -> dict:
    frame = load_feature_frame(Config.PREDICTION_HORIZON_DAYS)
    data, X, y, feature_cols = _prepare_xy(frame)

    unique_dates = sorted(data["date"].dt.date.unique())
    if len(unique_dates) < 120:
        raise RuntimeError("Se requieren mas fechas historicas para una validacion temporal razonable.")

    # Holdout temporal: ultimo 20 % de fechas como prueba.
    split_idx = max(1, int(len(unique_dates) * 0.8))
    split_date = unique_dates[split_idx]
    train_mask = data["date"].dt.date < split_date
    test_mask = ~train_mask

    X_train, y_train = X.loc[train_mask], y.loc[train_mask]
    X_test, y_test = X.loc[test_mask], y.loc[test_mask]

    model = XGBClassifier(
        n_estimators=350,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=2,
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)) if y_test.nunique() > 1 else None,
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "split_date": str(split_date),
        "feature_columns": feature_cols,
        "horizon_days": Config.PREDICTION_HORIZON_DAYS,
    }

    Config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "features": feature_cols,
        "horizon_days": Config.PREDICTION_HORIZON_DAYS,
        "trained_on": date.today().isoformat(),
    }
    joblib.dump(artifact, Config.MODEL_PATH)
    Config.MODEL_META_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    add_backtest_result({
        "ticker": "ALL",
        "run_date": date.today(),
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "roc_auc": metrics["roc_auc"],
        "notes": f"Holdout temporal desde {split_date}; horizonte {Config.PREDICTION_HORIZON_DAYS} dias de mercado.",
    })

    generate_latest_predictions(artifact)
    return metrics


def generate_latest_predictions(artifact: dict | None = None) -> list[dict]:
    if artifact is None:
        if not Config.MODEL_PATH.exists():
            raise RuntimeError("Modelo no encontrado. Ejecute python -m app.ml.train_xgboost")
        artifact = joblib.load(Config.MODEL_PATH)

    model = artifact["model"]
    feature_cols = artifact["features"]
    latest = latest_feature_rows(artifact.get("horizon_days", Config.PREDICTION_HORIZON_DAYS))
    latest = latest.dropna(subset=["ret_20", "ma_ratio_50", "volatility_20"]).copy()
    if latest.empty:
        raise RuntimeError("No hay features actuales suficientes para generar predicciones")

    X = latest.reindex(columns=feature_cols).replace([np.inf, -np.inf], np.nan)
    latest["probability_favorable"] = model.predict_proba(X)[:, 1]
    latest = latest.sort_values("probability_favorable", ascending=False).reset_index(drop=True)
    latest["rank_position"] = np.arange(1, len(latest) + 1)

    output = []
    for _, row in latest.iterrows():
        record = {
            "ticker": row["ticker"],
            "as_of_date": row["date"].date() if hasattr(row["date"], "date") else row["date"],
            "probability_favorable": float(row["probability_favorable"]),
            "sentiment_score": float(row.get("sentiment_score", 0.0) or 0.0),
            "model_version": "xgboost-v1",
            "horizon_days": int(artifact.get("horizon_days", Config.PREDICTION_HORIZON_DAYS)),
            "rank_position": int(row["rank_position"]),
        }
        upsert_prediction(record)
        output.append(record)
    return output


def walk_forward_validate(n_splits: int = 4) -> list[dict]:
    """Walk-forward simplificado por bloques temporales, sin mezclar futuro en entrenamiento."""
    frame = load_feature_frame(Config.PREDICTION_HORIZON_DAYS)
    data, X, y, feature_cols = _prepare_xy(frame)
    dates = sorted(data["date"].dt.date.unique())
    if len(dates) < 200:
        raise RuntimeError("Datos insuficientes para Walk-Forward. Se recomiendan varios anos de historico.")

    boundaries = np.linspace(int(len(dates) * 0.45), len(dates) - 1, n_splits + 1, dtype=int)
    results = []
    for i in range(n_splits):
        train_end = dates[boundaries[i]]
        test_end = dates[boundaries[i + 1]]
        train_mask = data["date"].dt.date <= train_end
        test_mask = (data["date"].dt.date > train_end) & (data["date"].dt.date <= test_end)
        if test_mask.sum() == 0:
            continue

        model = XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42,
            n_jobs=2,
        )
        model.fit(X.loc[train_mask, feature_cols], y.loc[train_mask])
        p = model.predict_proba(X.loc[test_mask, feature_cols])[:, 1]
        y_true = y.loc[test_mask]
        results.append({
            "window": i + 1,
            "train_end": str(train_end),
            "test_end": str(test_end),
            "rows": int(test_mask.sum()),
            "accuracy": float(accuracy_score(y_true, (p >= 0.5).astype(int))),
            "roc_auc": float(roc_auc_score(y_true, p)) if y_true.nunique() > 1 else None,
        })
    return results


if __name__ == "__main__":
    print(json.dumps(train_model(), indent=2))
