import duckdb

def test_driver_season_performance_aggregation(
    parquet_test_data
):

    con = duckdb.connect()

    query = f"""
    WITH season_driver_metrics AS (

        SELECT
            season,
            driverId,

            COUNT(*) AS races_entered,

            SUM(
                CASE
                    WHEN positionOrder = 1
                    THEN 1
                    ELSE 0
                END
            ) AS wins,

            SUM(
                CASE
                    WHEN positionOrder <= 3
                    THEN 1
                    ELSE 0
                END
            ) AS podiums,

            SUM(
                CASE
                    WHEN fastest_lap_rank = 1
                    THEN 1
                    ELSE 0
                END
            ) AS fastest_laps,

            SUM(points) AS total_points

        FROM read_parquet(
            '{parquet_test_data["race_results"]}'
        )

        GROUP BY
            season,
            driverId
    ),

    final_driver_standings AS (

        SELECT
            season,
            driverId,
            position AS championship_position

        FROM read_parquet(
            '{parquet_test_data["driver_standings"]}'
        )
    )

    SELECT

        m.*,

        d.forename,
        d.surname,

        s.championship_position

    FROM season_driver_metrics m

    LEFT JOIN read_parquet(
        '{parquet_test_data["drivers"]}'
    ) d
        ON m.driverId = d.driverId

    LEFT JOIN final_driver_standings s
        ON m.driverId = s.driverId
       AND m.season = s.season
    """

    result = con.execute(query).pl()

    row = result.row(0, named=True)

    assert row["season"] == 2024
    assert row["driverId"] == "max_verstappen"
    assert row["races_entered"] == 1
    assert row["wins"] == 1
    assert row["podiums"] == 1
    assert row["fastest_laps"] == 1
    assert row["total_points"] == 25.0
    assert row["championship_position"] == 1
    assert row["forename"] == "Max"
    assert row["surname"] == "Verstappen"