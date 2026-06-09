import os

import pytest
import requests
from f1_api_ingestion import ADLSUPLOADER, F1CLIENT


@pytest.mark.integration
def test_live_api_contract_verification():
    """Smoke test running against the actual live Jolpica API to verify contract stability."""
    client = F1CLIENT()
    try:
        data = client.fetch_season_results(2024)
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Live API call failed entirely: {e}")

    # Structural validations on live JSON response
    assert "MRData" in data
    assert "RaceTable" in data["MRData"]
    assert "Races" in data["MRData"]["RaceTable"]
    assert len(data["MRData"]["RaceTable"]["Races"]) > 0


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("STORAGE_ACCOUNT_NAME") is None,
    reason="Skipping live Azure test; STORAGE_ACCOUNT_NAME environment variable not set.",
)
def test_live_azure_connectivity_and_upload():
    """Attempts a real raw upload to your development Azure Data Lake tier."""
    account_name = os.environ["STORAGE_ACCOUNT_NAME"]
    container_name = os.getenv("CONTAINER_NAME", "bronze")

    test_blob_path = "test_integration/smoke_test.json"
    test_payload = {"status": "integration_test_active", "engine": "pytest"}

    try:
        uploader = ADLSUPLOADER(storage_account_name=account_name, container_name=container_name)
        uploader.upload_json(data=test_payload, blob_path=test_blob_path)
    except Exception as e:
        pytest.fail(f"Actual connection setup to ADLS Gen2 container failed: {e}")
