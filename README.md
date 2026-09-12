# Sistema Autónomo de Análisis Predictivo de Mercados Financieros

Proyecto académico de Business Analytics para **inversión a largo plazo**. Integra datos de mercado, macroeconomía, fundamentales y noticias; usa **FinBERT** para sentimiento financiero, **XGBoost** para estimar una probabilidad de rendimiento favorable y expone resultados mediante **Flask REST API** para consumo desde **Power BI Service**.

> Uso académico y analítico. No ejecuta operaciones bursátiles ni constituye una recomendación financiera personalizada.

## Arquitectura

```text
Yahoo Finance / Alpha Vantage ─┐
FRED ──────────────────────────┤
SEC EDGAR ─────────────────────┼─> Python ETL -> MySQL
GDELT ─> Hugging Face FinBERT ─┘                    |
                                                   v
                                         Features + XGBoost
                                         Walk-Forward / evaluación
                                                   |
                                                   v
                                               MySQL
                                                   |
                                                   v
                                      Flask API en Railway
                                                   |
                                                   v
                                         Power BI Service
```

## Tecnologías

- Python, Pandas, NumPy
- Scikit-learn, XGBoost
- Hugging Face Inference Providers + `ProsusAI/finbert`
- MySQL + SQLAlchemy + PyMySQL
- Flask + Gunicorn
- Railway: API, MySQL y Cron Job
- Power BI Desktop / Power Query / DAX / Power BI Service

## Estructura

```text
.
├── app/
│   ├── ml/
│   │   ├── features.py
│   │   └── train_xgboost.py
│   ├── services/
│   │   ├── fred.py
│   │   ├── gdelt.py
│   │   ├── huggingface_finbert.py
│   │   ├── market.py
│   │   └── sec_edgar.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── repository.py
│   └── routes.py
├── jobs/run_pipeline.py
├── scripts/
│   ├── check_connections.py
│   ├── init_db.py
│   └── seed_demo.py
├── powerbi/
│   ├── PowerQuery_Ranking.m
│   ├── PowerQuery_History.m
│   └── DAX_Medidas.txt
├── docs/
│   ├── ARQUITECTURA.md
│   ├── HUGGING_FACE.md
│   ├── POWER_BI_SERVICE.md
│   └── RAILWAY.md
├── .railway/SETTINGS.md
├── Procfile
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Ejecución local

### 1. Crear entorno

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Por defecto, si no cambias `DATABASE_URL`, puedes utilizar SQLite para una prueba rápida cambiando en `.env`:

```text
DATABASE_URL=sqlite:///local_inversion_bi.db
```

### 2. Inicializar la base

```bash
python scripts/init_db.py
```

### 3. Prueba rápida sin APIs externas

```bash
python scripts/seed_demo.py
python main.py
```

Abre:

```text
http://127.0.0.1:5000/api/health
http://127.0.0.1:5000/api/dashboard
```

Los valores generados por `seed_demo.py` son **sintéticos**.

## Pipeline real

Configura en `.env` al menos:

```text
DATABASE_URL=...
HF_TOKEN=...
FRED_API_KEY=...
SEC_USER_AGENT=Nombre proyecto correo@ejemplo.com
```

Luego:

```bash
python jobs/run_pipeline.py
```

El pipeline:

1. descarga precios históricos;
2. carga indicadores FRED;
3. obtiene fundamentales de SEC EDGAR;
4. obtiene noticias GDELT;
5. clasifica titulares con FinBERT en Hugging Face;
6. construye variables;
7. entrena XGBoost;
8. realiza holdout temporal y Walk-Forward simplificado;
9. genera ranking y guarda predicciones en MySQL.

## Endpoints

| Método | Endpoint | Función |
|---|---|---|
| GET | `/api/health` | Salud del servicio |
| GET | `/api/assets` | Activos disponibles |
| GET | `/api/dashboard` | Ranking y KPI principales |
| GET | `/api/predict/<ticker>` | Última predicción guardada |
| GET | `/api/sentiment/<ticker>` | Sentimiento agregado reciente |
| POST | `/api/sentiment/analyze` | Prueba directa de FinBERT |
| GET | `/api/pbi/dashboard` | Dataset plano para Power BI |
| GET | `/api/pbi/history` | Histórico para Power BI |

## Despliegue

Lee en este orden:

1. `docs/RAILWAY.md`
2. `docs/HUGGING_FACE.md`
3. `docs/POWER_BI_SERVICE.md`
4. `docs/ARQUITECTURA.md`

## Variables principales de Railway

```text
DATABASE_URL=${{MySQL.MYSQL_URL}}
HF_TOKEN=...
HF_MODEL=ProsusAI/finbert
HF_PROVIDER=hf-inference
FRED_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
SEC_USER_AGENT=...
PBI_API_KEY=...
TICKERS=AAPL,MSFT,NVDA,AMZN,GOOGL,SPY,QQQ
PREDICTION_HORIZON_DAYS=126
```

## Power BI

El proyecto evita exponer MySQL públicamente. Power BI consume una API HTTPS de Railway. Copia las consultas M incluidas en `powerbi/` y usa la credencial **Web API** para `PBI_API_KEY`.

## Observaciones técnicas

- `PREDICTION_HORIZON_DAYS=126` representa aproximadamente seis meses bursátiles y puede modificarse.
- El código soporta datos faltantes en macroeconomía/fundamentales; XGBoost puede trabajar con `NaN`.
- GDELT puede tener tiempos de espera. El pipeline registra el error y continúa con el resto de fuentes.
- El modelo guardado en filesystem no se comparte entre servicios Railway; los **resultados** sí se comparten porque se guardan en MySQL.
- Para un entorno de producción real convendría añadir migraciones Alembic, pruebas de datos, observabilidad, control de costes y una estrategia formal de versionado de modelos.
"# prueba.bi" 
