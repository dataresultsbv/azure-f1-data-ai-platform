import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from f1_api_ingestion import F1CLIENT, ADLSUPLOADER, INGESTIONPIPELINE

# ==============================================================================
# F1CLIENT UNIT TESTS
# ==============================================================================

@patch("f1_api_ingestion.requests.get")
def test_f1_client_fetch_season_results_success(mock_get, sample_f1_json):
    """Verifies F1CLIENT correctly targets the API endpoint and handles parameters."""
    mock_response = MagicMock()
    mock_response.json.return_value = sample_f1_json
    mock_get.return_value = mock_response

    client = F1CLIENT(timeout=5)
    data = client.fetch_season_results(2024)

    assert data == sample_f1_json
    mock_get.assert_called_once_with(
        "https://api.jolpi.ca/ergast/f1/2024/results.json",
        params={"limit": 1000},
        timeout=5
    )

@patch("f1_api_ingestion.requests.get")
def test_f1_client_handles_http_errors(mock_get):
    """Ensures API errors correctly bubble up via raise_for_status."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
    mock_get.return_value = mock_response

    client = F1CLIENT()
    with pytest.raises(HTTPError):
        client.fetch_season_results(1920)


# ==============================================================================
# ADLSUPLOADER UNIT TESTS
# ==============================================================================

@patch("f1_api_ingestion.BlobServiceClient")
@patch("f1_api_ingestion.DefaultAzureCredential")
def test_adls_uploader_initialization(mock_cred, mock_blob_service):
    """Verifies that the ADLS client instantiates correctly with the proper URL template."""
    mock_container_client = MagicMock()
    mock_blob_service.return_value.get_container_client.return_value = mock_container_client

    uploader = ADLSUPLOADER(storage_account_name="testsa", container_name="testcontainer")
    
    assert uploader.container_client == mock_container_client
    mock_blob_service.assert_called_once_with(
        "https://testsa.blob.core.windows.net", 
        credential=mock_cred.return_value
    )


# ==============================================================================
# INGESTIONPIPELINE ORCHESTRATOR UNIT TESTS
# ==============================================================================

def test_pipeline_orchestrator_happy_path(mock_api_client, mock_uploader):
    """Verifies that for a 1-year range, all 3 extractions run and upload to the right paths."""
    pipeline = INGESTIONPIPELINE(
        start_season=2024, 
        end_season=2024, 
        api_client=mock_api_client, 
        uploader=mock_uploader
    )
    pipeline.run()

    # Check API execution counts
    mock_api_client.fetch_season_results.assert_called_once_with(2024)
    mock_api_client.fetch_driver_standings.assert_called_once_with(2024)
    mock_api_client.fetch_constructor_standings.assert_called_once_with(2024)

    # Check Azure Upload routes
    assert mock_uploader.upload_json.call_count == 3
    mock_uploader.upload_json.assert_any_call(
        {"dataType": "results"}, 
        "f1/results/season=2024/bronze_results_2024.json"
    )

def test_pipeline_resilience_on_partial_failure(mock_api_client, mock_uploader):
    """Verifies that if one endpoint breaks, the pipeline moves on to the next endpoints."""
    # Simulate API failure ONLY on results endpoint
    mock_api_client.fetch_season_results.side_effect = RuntimeError("API Dead")

    pipeline = INGESTIONPIPELINE(
        start_season=2024, 
        end_season=2024, 
        api_client=mock_api_client, 
        uploader=mock_uploader
    )
    
    # Run should complete without throwing an unhandled exception due to try-except blocks
    pipeline.run()

    # Driver and Constructor standings should still have tried to run and upload
    mock_api_client.fetch_driver_standings.assert_called_once_with(2024)
    assert mock_uploader.upload_json.call_count == 2