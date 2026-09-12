# Ajustes actuales de Railway (2026)

Railway depreco `railway.json` / `railway.toml` para servicios nuevos. Este proyecto se configura desde el Dashboard o con la CLI/IaC actual.

## Servicio `inversion-api`

- Source: este repositorio GitHub.
- Build: Dockerfile detectado automaticamente.
- Start Command: dejar el `CMD` del Dockerfile, o configurar manualmente:

```text
/bin/sh -c "gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 main:app"
```

- Healthcheck Path: `/api/health`
- Public Networking: Generate Domain.
- Variables: `DATABASE_URL`, `HF_TOKEN`, `FRED_API_KEY`, `SEC_USER_AGENT`, `PBI_API_KEY`, etc.

## Servicio `inversion-pipeline`

- Source: el mismo repositorio GitHub.
- Build: Dockerfile detectado automaticamente.
- Start Command:

```text
python jobs/run_pipeline.py
```

- Cron Schedule sugerido para largo plazo:

```text
0 5 * * 1
```

Railway evalua cron en UTC. El proceso debe terminar cuando finalice el pipeline.

## MySQL

Agrega un servicio MySQL dentro del mismo proyecto y referencia su URL privada:

```text
DATABASE_URL=${{MySQL.MYSQL_URL}}
```

Si el servicio tiene otro nombre, cambia `MySQL` por ese nombre.
