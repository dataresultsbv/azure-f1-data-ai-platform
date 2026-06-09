from f1_to_gold import GoldAggregationConfig, GoldAggregationEngine


def test_extract_account_name(monkeypatch):

    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://f1storage.dfs.core.windows.net")

    config = GoldAggregationConfig()

    assert config.account_name == "f1storage"


def test_config_reads_environment_variables(monkeypatch):

    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://f1storage.dfs.core.windows.net")

    monkeypatch.setenv("START_SEASON", "2020")

    monkeypatch.setenv("END_SEASON", "2024")

    config = GoldAggregationConfig()

    assert config.start_season == 2020
    assert config.end_season == 2024


def test_engine_builds_storage_paths(mock_config, mock_client):

    engine = GoldAggregationEngine(mock_config, mock_client)

    assert "race_results" in engine.silver_race_results

    assert "driver_standings" in engine.silver_driver_standings

    assert "drivers" in engine.silver_drivers

    assert "gold" in engine.gold_destination


def test_process_executes_duckdb_query(engine, mock_client):

    engine.process()

    mock_client.execute_query.assert_called_once()


def test_process_generates_driver_metrics_sql(engine, mock_client):

    engine.process()

    sql = mock_client.execute_query.call_args[0][0]

    assert "season_driver_metrics" in sql

    assert "COUNT(*) AS races_entered" in sql

    assert "SUM(rr.points)" in sql

    assert "positionOrder = 1" in sql

    assert "championship_position" in sql
