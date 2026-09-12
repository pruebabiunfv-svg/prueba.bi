let
    ApiBaseUrl = "https://TU-SERVICIO.up.railway.app",
    Source = Json.Document(
        Web.Contents(
            ApiBaseUrl,
            [
                RelativePath = "api/pbi/history",
                Query = [days = "365"],
                ApiKeyName = "api_key",
                Timeout = #duration(0, 0, 2, 0)
            ]
        )
    ),
    AsTable = Table.FromList(Source, Splitter.SplitByNothing(), {"Record"}, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(
        AsTable,
        "Record",
        {"ticker", "as_of_date", "probability_favorable", "probability_pct", "sentiment_score", "model_version", "horizon_days", "rank_position"},
        {"Ticker", "Fecha", "ProbabilidadFavorable", "ProbabilidadPct", "SentimientoScore", "Modelo", "HorizonteDias", "Ranking"}
    ),
    Typed = Table.TransformColumnTypes(
        Expanded,
        {
            {"Ticker", type text},
            {"Fecha", type date},
            {"ProbabilidadFavorable", type number},
            {"ProbabilidadPct", type number},
            {"SentimientoScore", type number},
            {"Modelo", type text},
            {"HorizonteDias", Int64.Type},
            {"Ranking", Int64.Type}
        }
    )
in
    Typed
