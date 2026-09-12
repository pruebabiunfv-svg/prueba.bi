# Despliegue en Railway (flujo vigente en 2026)

## Estructura objetivo

En un solo proyecto Railway crea tres servicios:

```text
Proyecto Railway
├── MySQL
├── inversion-api       -> Flask / Gunicorn / HTTPS
└── inversion-pipeline  -> Cron Job / ETL + FinBERT + XGBoost
```

> Nota de 2026: Railway depreco `railway.json`/`railway.toml` para servicios nuevos. Por eso este ZIP usa Dockerfile y configuracion del Dashboard para Start Command, healthcheck y cron. Railway tambien ofrece Infrastructure as Code mediante `.railway/railway.ts` si luego deseas automatizar toda la infraestructura.

## A. Subir el codigo a GitHub

```bash
git init
git add .
git commit -m "Proyecto BI inversion"
git branch -M main
git remote add origin TU_REPOSITORIO
git push -u origin main
```

No subas `.env`.

## B. Crear proyecto y API

1. Railway > New Project > Deploy from GitHub repo.
2. Selecciona el repositorio.
3. Nombra el servicio `inversion-api`.
4. Railway detectara el `Dockerfile` de la raiz y construira la imagen.
5. En Settings > Deploy, puedes dejar el CMD del Dockerfile o definir Start Command:

```text
/bin/sh -c "gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 main:app"
```

6. Configura Healthcheck Path:

```text
/api/health
```

7. Settings > Networking > Generate Domain.

Railway inyecta `PORT`; el contenedor escucha en ese puerto.

## C. Agregar MySQL

En el canvas:

1. `+ New` > Database > MySQL.
2. Railway crea variables como `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE` y `MYSQL_URL`.
3. En `inversion-api` define:

```text
DATABASE_URL=${{MySQL.MYSQL_URL}}
```

Si el servicio de base de datos tiene otro nombre, usa ese nombre en la referencia.

No necesitas habilitar acceso publico a MySQL para que la API y el Cron se conecten dentro del mismo proyecto.

## D. Variables del API

Ejemplo:

```text
DATABASE_URL=${{MySQL.MYSQL_URL}}
HF_TOKEN=...
HF_MODEL=ProsusAI/finbert
HF_PROVIDER=hf-inference
FRED_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
SEC_USER_AGENT=Proyecto universitario correo@ejemplo.com
PBI_API_KEY=...
TICKERS=AAPL,MSFT,NVDA,AMZN,GOOGL,SPY,QQQ
PREDICTION_HORIZON_DAYS=126
```

Guarda secretos solo en Variables de Railway.

## E. Inicializar y probar

Las tablas se crean de forma idempotente cuando inicia Flask, por lo que normalmente no necesitas un paso de migracion inicial.

Si deseas ejecutar utilidades dentro del contenedor ya desplegado, entra por SSH:

```bash
railway ssh --service inversion-api
python scripts/check_connections.py
```

Para verificar la interfaz antes de cargar datos reales, dentro de esa sesion puedes ejecutar:

```bash
python scripts/seed_demo.py
```

Los datos de `seed_demo.py` son sinteticos. Evita usar `railway run` para acceder a una base que solo usa red privada, porque ese comando ejecuta el proceso en tu maquina local con las variables de Railway.

## F. Crear el Cron Job

1. Crea un segundo servicio desde el MISMO repositorio y llamalo `inversion-pipeline`.
2. En Settings > Deploy > Start Command define:

```text
python jobs/run_pipeline.py
```

3. En Settings > Cron Schedule define, por ejemplo:

```text
0 5 * * 1
```

Esto ejecuta el pipeline semanalmente los lunes a las 05:00 UTC. Railway evalua los cron en UTC y espera que el proceso termine al finalizar la tarea.

4. Agrega las mismas referencias/secretos necesarios:

```text
DATABASE_URL=${{MySQL.MYSQL_URL}}
HF_TOKEN=...
FRED_API_KEY=...
SEC_USER_AGENT=...
TICKERS=...
```

No generes dominio publico para el Cron Job.

## G. Pipeline ejecutado

```text
1. Yahoo Finance -> market_prices
2. FRED -> macro_indicators
3. SEC EDGAR -> fundamentals
4. GDELT -> noticias
5. Hugging Face FinBERT -> news_sentiment
6. Features -> XGBoost
7. Holdout temporal + Walk-Forward
8. Predicciones -> predictions
9. Flask expone resultados a Power BI
```

## H. Comprobaciones

```text
GET /api/health
GET /api/dashboard
GET /api/predict/MSFT
GET /api/pbi/dashboard?api_key=TU_CLAVE
```

## Referencias oficiales

- https://docs.railway.com/guides/flask
- https://docs.railway.com/databases/mysql
- https://docs.railway.com/variables
- https://docs.railway.com/builds/dockerfiles
- https://docs.railway.com/deployments/healthchecks
- https://docs.railway.com/cron-jobs
- https://docs.railway.com/config-as-code
