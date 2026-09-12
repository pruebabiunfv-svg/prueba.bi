# Arquitectura de despliegue

```text
Yahoo Finance / Alpha Vantage    FRED       SEC EDGAR       GDELT
            |                      |            |              |
            +----------------------+------------+--------------+
                                   |
                         Railway Cron Job
                     Python + Pandas + NumPy
                                   |
                       Hugging Face FinBERT
                         (inferencia remota)
                                   |
                              MySQL Railway
                                   |
                    XGBoost + Walk-Forward
                     + predicciones/ranking
                                   |
                              MySQL Railway
                                   |
                    Railway Flask REST API
                         HTTPS publico
                                   |
                           Power BI Service
                     KPI + ranking + historico
```

## Servicios Railway recomendados

1. **MySQL**: persistencia comun para API y pipeline.
2. **API Flask**: servicio persistente y dominio HTTPS publico.
3. **Pipeline**: segundo servicio desde el mismo repositorio, configurado como Cron Job desde Settings > Deploy y Settings > Cron Schedule.

El Cron Job no necesita compartir el filesystem con la API. Entrena y calcula resultados, pero el dato que consume la API se persiste en MySQL (`predictions`, `news_sentiment`, etc.).

## Decisiones de arquitectura

- FinBERT se consume por Hugging Face Inference Providers para evitar alojar el modelo completo dentro del contenedor Flask.
- MySQL permanece privado dentro de Railway. Power BI consume la API HTTPS, no el puerto MySQL.
- El API ofrece endpoints planos `/api/pbi/*` para simplificar Power Query.
- No hay ejecucion automatica de operaciones bursatiles: el sistema es analitico y de apoyo academico a decisiones.
