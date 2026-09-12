# Power BI Desktop -> Power BI Service

El enfoque recomendado es consumir la API HTTPS desplegada en Railway, no abrir MySQL a Internet.

## 1. Preparar el endpoint

Railway debe exponer un dominio parecido a:

```text
https://mi-api.up.railway.app
```

Verifica:

```text
https://mi-api.up.railway.app/api/health
```

Para Power BI se usan:

```text
/api/pbi/dashboard
/api/pbi/history
```

## 2. Proteger con clave

En Railway define:

```text
PBI_API_KEY=una_clave_larga_y_unica
```

La API acepta esa clave como parametro `api_key`. Esto permite usar `ApiKeyName` de Power Query y evitar escribir el secreto dentro del archivo M.

## 3. Power BI Desktop

1. Abre Power BI Desktop.
2. Transformar datos > Nueva fuente > Consulta en blanco.
3. Editor avanzado.
4. Copia `powerbi/PowerQuery_Ranking.m`.
5. Cambia `ApiBaseUrl` por el dominio de Railway.
6. Al solicitar credenciales, selecciona **Web API** e ingresa solo el valor de `PBI_API_KEY`.
7. Renombra la consulta como `Ranking`.
8. Repite con `PowerQuery_History.m` si deseas historico.
9. Copia las medidas de `DAX_Medidas.txt`.

`Web.Contents` usa `RelativePath` para mantener estable la fuente base y `ApiKeyName="api_key"` para que el secreto se gestione como credencial.

## 4. Publicar en Power BI Service

1. Guarda el `.pbix`.
2. Selecciona **Publicar** y el workspace.
3. En Power BI Service abre el modelo semantico.
4. Revisa **Data source credentials** y configura la credencial Web API si es solicitada.
5. En **Refresh > Schedule refresh**, define la frecuencia.

Al consumir una API HTTPS publica en la nube, normalmente no es necesario exponer MySQL ni instalar un gateway local. La necesidad exacta de gateway depende de la configuracion y del tipo de fuente/credencial de tu entorno de Power BI.

## 5. Orden de actualizacion sugerido

Para largo plazo:

1. Railway Cron actualiza datos y predicciones.
2. Esperar a que termine el pipeline.
3. Power BI Service actualiza el modelo semantico despues.

Ejemplo academico:

- Cron Railway: lunes 05:00 UTC.
- Power BI Service: programar refresh posteriormente, segun las opciones disponibles en tu licencia/workspace.

## Referencias oficiales

- https://learn.microsoft.com/powerquery-m/web-contents
- https://learn.microsoft.com/power-query/connectors/web/web
- https://learn.microsoft.com/power-bi/connect-data/refresh-scheduled-refresh
