import pytest
import polars as pl
from unittest.mock import MagicMock

@pytest.fixture
def mock_bronze_results_json() -> bytes:
    """Simulates raw bytes downloaded from the Bronze container."""
    return b"""
    {
        "MRData": {
            "RaceTable": {
                "Races": [
                    {
                        "season": "2024",
                        "round": "1",
                        "raceName": "Bahrain Grand Prix",
                        "Circuit": {
                            "circuitId": "bahrain",
                            "circuitName": "Bahrain International Circuit",
                            "url": "http://mock.url",
                            "Location": {"locality": "Sakhir", "country": "Bahrain", "lat": "26.0325", "long": "50.5106"}
                        },
                        "date": "2024-03-02",
                        "time": "15:00:00Z",
                        "url": "http://mock-race.url",
                        "Results": [
                            {
                                "number": "1",
                                "position": "1",
                                "positionText": "1",
                                "points": "25",
                                "grid": "1",
                                "laps": "57",
                                "status": "Finished",
                                "Driver": {
                                    "driverId": "max_verstappen",
                                    "code": "VER",
                                    "permanentNumber": "1",
                                    "givenName": "Max",
                                    "familyName": "Verstappen",
                                    "dateOfBirth": "1997-09-30",
                                    "nationality": "Dutch",
                                    "url": "http://ver.url"
                                },
                                "Constructor": {
                                    "constructorId": "red_bull",
                                    "name": "Red Bull",
                                    "nationality": "Austrian",
                                    "url": "http://rb.url"
                                },
                                "FastestLap": {
                                    "rank": "1",
                                    "Time": {"time": "1:32.608"},
                                    "AverageSpeed": {"speed": "210.2"}
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
    """