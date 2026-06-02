import pytest
import polars as pl
from unittest.mock import MagicMock

from f1_to_gold import (
    GoldAggregationConfig,
    GoldAggregationEngine,
)


@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setenv(
        "AZURE_STORAGE_ACCOUNT_URL",
        "https://myaccount.dfs.core.windows.net"
    )

    monkeypatch.setenv(
        "BLOB_CONTAINER_NAME",
        "silver"
    )

    monkeypatch.setenv(
        "START_SEASON",
        "2024"
    )

    monkeypatch.setenv(
        "END_SEASON",
        "2025"
    )

    return GoldAggregationConfig()


@pytest.fixture
def mock_client():
    client = MagicMock()
    return client


@pytest.fixture
def engine(mock_config, mock_client):
    return GoldAggregationEngine(
        config=mock_config,
        client=mock_client
    )


@pytest.fixture
def race_results_df():

    return pl.DataFrame({
        "season": [2024],
        "driverId": ["max_verstappen"],
        "positionOrder": [1],
        "fastest_lap_rank": [1],
        "points": [25.0],
        "grid": [1],
        "status": ["Finished"]
    })


@pytest.fixture
def driver_standings_df():

    return pl.DataFrame({
        "season": [2024],
        "round": [1],
        "driverId": ["max_verstappen"],
        "position": [1],
        "points": [25.0],
        "wins": [1]
    })


@pytest.fixture
def drivers_df():

    return pl.DataFrame({
        "driverId": ["max_verstappen"],
        "forename": ["Max"],
        "surname": ["Verstappen"],
        "nationality": ["Dutch"]
    })


@pytest.fixture
def parquet_test_data(
    tmp_path,
    race_results_df,
    driver_standings_df,
    drivers_df
):

    race_results_path = tmp_path / "race_results.parquet"
    driver_standings_path = tmp_path / "driver_standings.parquet"
    drivers_path = tmp_path / "drivers.parquet"

    race_results_df.write_parquet(race_results_path)

    driver_standings_df.write_parquet(
        driver_standings_path
    )

    drivers_df.write_parquet(
        drivers_path
    )

    return {
        "race_results": race_results_path,
        "driver_standings": driver_standings_path,
        "drivers": drivers_path,
    }