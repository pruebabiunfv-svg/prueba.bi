# Conexion con Hugging Face / FinBERT

## Objetivo

Usar `ProsusAI/finbert` para convertir titulares/noticias financieras en:

- `positive`
- `neutral`
- `negative`
- `sentiment_score = P(positive) - P(negative)`, en un rango aproximado de -1 a 1.

## 1. Crear token

1. Inicia sesion en Hugging Face.
2. Abre Settings > Access Tokens.
3. Crea un token apropiado para inferencia.
4. No lo guardes en GitHub ni dentro del codigo.

## 2. Variable en Railway

En el servicio API y en el servicio Cron agrega:

```text
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
HF_MODEL=ProsusAI/finbert
HF_PROVIDER=hf-inference
HF_TIMEOUT_SECONDS=45
```

El proyecto usa `huggingface_hub.InferenceClient`:

```python
client = InferenceClient(
    provider="hf-inference",
    api_key=os.environ["HF_TOKEN"],
)
output = client.text_classification(text, model="ProsusAI/finbert")
```

## 3. Probar localmente

```bash
python scripts/check_connections.py
```

O con la API:

```bash
curl -X POST http://127.0.0.1:5000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"The company reported stronger revenue and higher margins."}'
```

## 4. Flujo GDELT -> FinBERT

`jobs/run_pipeline.py` obtiene titulares con GDELT y envia cada titular a Hugging Face. El resultado se almacena en `news_sentiment`.

Si `HF_TOKEN` no existe, el pipeline omite el sentimiento. Para demostraciones controladas existe `HF_ALLOW_NEUTRAL_FALLBACK=true`, pero ese fallback debe considerarse dato sintetico, no resultado FinBERT.

## Referencias oficiales

- https://huggingface.co/docs/huggingface_hub/package_reference/inference_client
- https://huggingface.co/docs/inference-providers/tasks/text-classification
- https://huggingface.co/ProsusAI/finbert
