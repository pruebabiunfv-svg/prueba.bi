let
    // Reemplaza solo el dominio. Mantener una URL base fija ayuda al refresh en Power BI Service.
    ApiBaseUrl = "https://TU-SERVICIO.up.railway.app",

    // NO escribir la clave aqui. Power BI pedira el valor de PBI_API_KEY como credencial Web API.
    Source = Json.Document(
        Web.Contents(
            ApiBaseUrl,
            [
                RelativePath = "api/pbi/dashboard",
                ApiKeyName = "api_key",
                Timeout = #duration(0, 0, 2, 0)
            ]
        )
    ),

    AsTable = Table.FromList(Source, Splitter.SplitByNothing(), {"Record"}, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(
        AsTable,
        "Record",
        {"Ticker", "Fecha", "Ranking", "ProbabilidadFavorable", "ProbabilidadPct", "SentimientoScore", "HorizonteDias", "Modelo", "UltimoPrecio", "FechaMercado"},
        {"Ticker", "Fecha", "Ranking", "ProbabilidadFavorable", "ProbabilidadPct", "SentimientoScore", "HorizonteDias", "Modelo", "UltimoPrecio", "FechaMercado"}
    ),
    Typed = Table.TransformColumnTypes(
        Expanded,
        {
            {"Ticker", type text},
            {"Fecha", type date},
            {"Ranking", Int64.Type},
            {"ProbabilidadFavorable", type number},
            {"ProbabilidadPct", type number},
            {"SentimientoScore", type number},
            {"HorizonteDias", Int64.Type},
            {"Modelo", type text},
            {"UltimoPrecio", type number},
            {"FechaMercado", type date}
        }
    )
in
    Typed
