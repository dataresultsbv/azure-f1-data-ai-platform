import pytest
from unittest.mock import MagicMock

@pytest.fixture
def sample_f1_json():
    return {
        "MRData": {
            "total": "1",
            "RaceTable": {
                "season": "2024",
                "Races": [
                    {
                        "round": "1",
                        "raceName": "Bahrain Grand Prix"
                    }
                ]
            }
        }
    }

@pytest.fixture
def mock_api_client():
    """Returns an F1CLIENT with mocked methods."""
    client = MagicMock()
    client.fetch_season_results.return_value = {"dataType": "results"}
    client.fetch_driver_standings.return_value = {"dataType": "driver_standings"}
    client.fetch_constructor_standings.return_value = {"dataType": "constructor_standings"}
    return client

@pytest.fixture
def mock_uploader():
    """Returns a completely mocked ADLSUPLOADER."""
    return MagicMock()