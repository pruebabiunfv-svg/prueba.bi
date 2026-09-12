# Modelos generados

Este directorio se usa para guardar los artefactos de XGBoost creados por `python -m app.ml.train_xgboost`.

Los archivos `.joblib` y metadatos `.json` no se versionan por defecto. En Railway el almacenamiento del contenedor es efimero; para un proyecto academico sencillo puede regenerarse el modelo con un Cron Job. Para persistencia estricta, usar un volumen o almacenamiento externo.
