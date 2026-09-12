from dataclasses import dataclass
from typing import List
from huggingface_hub import InferenceClient
from app.config import Config


@dataclass
class SentimentResult:
    label: str
    score: float
    probabilities: dict
    inference_source: str


def _normalize_label(label: str) -> str:
    value = (label or "").strip().lower()
    mapping = {
        "positive": "positive",
        "neutral": "neutral",
        "negative": "negative",
        "label_0": "positive",
        "label_1": "negative",
        "label_2": "neutral",
    }
    return mapping.get(value, value or "neutral")


def _signed_score(probabilities: dict) -> float:
    """Score financiero en [-1, 1]: P(positivo) - P(negativo)."""
    return float(probabilities.get("positive", 0.0) - probabilities.get("negative", 0.0))


def classify_financial_text(text: str) -> SentimentResult:
    """
    Clasifica texto financiero con FinBERT usando Hugging Face Inference Providers.
    No descarga el modelo de ~438 MB dentro de Railway.
    """
    if not text or not text.strip():
        raise ValueError("El texto no puede estar vacio")

    if not Config.HF_TOKEN:
        if Config.HF_ALLOW_NEUTRAL_FALLBACK:
            return SentimentResult(
                label="neutral",
                score=0.0,
                probabilities={"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                inference_source="fallback",
            )
        raise RuntimeError("HF_TOKEN no esta configurado")

    client = InferenceClient(
        provider=Config.HF_PROVIDER,
        api_key=Config.HF_TOKEN,
        timeout=Config.HF_TIMEOUT_SECONDS,
    )
    output = client.text_classification(text[:2500], model=Config.HF_MODEL)

    probabilities = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    for item in output:
        label = _normalize_label(getattr(item, "label", ""))
        score = float(getattr(item, "score", 0.0))
        if label in probabilities:
            probabilities[label] = score

    best_label = max(probabilities, key=probabilities.get)
    return SentimentResult(
        label=best_label,
        score=_signed_score(probabilities),
        probabilities=probabilities,
        inference_source="huggingface",
    )


def classify_many(texts: List[str]) -> List[SentimentResult]:
    return [classify_financial_text(text) for text in texts]
