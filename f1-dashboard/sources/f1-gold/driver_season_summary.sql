SELECT 
    *, 
    CAST(season AS INT) AS season_clean 
FROM read_parquet('sources/f1-gold/driver_season_summary.parquet');