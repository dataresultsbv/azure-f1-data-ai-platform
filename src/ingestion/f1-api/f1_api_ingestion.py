import os
import json
import logging
import sys
import requests
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class F1CLIENT:
    """Responsable for all comunication with the jolpica-f1-api."""
    
    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_season_results(self, season: int) -> Dict[str, Any]:
        """Retrieves race results for a specific season."""
        url = f"{self.BASE_URL}/{season}/results.json"
        params = {"limit": 1000}
        
        logger.info(f"Connecting to API for season {season} -> {url}")
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        total_results = data.get("MRData", {}).get("total", 0)
        logger.info(f"SUCCES - HTTP {response.status_code} | Records: {total_results}")
        
        return data


class ADLSUPLOADER:
    """Responsable for connecting and laoding data to Azure Storage."""

    def __init__(self, storage_account_name: str, container_name: str):
        self.storage_account_name = storage_account_name
        self.container_name = container_name
        self.container_client = self._initialize_client()

    def _initialize_client(self):
        """Initializeses the Azure Blob Service Client using DefaultAzureCredential."""
        account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
        try:
            credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(account_url, credential=credential)
            return blob_service_client.get_container_client(self.container_name)
        except Exception as e:
            logger.critical(f"CRITICAL ERROR - Failed to initialize Azure Client: {e}")
            raise

    def upload_json(self, data: Dict[str, Any], blob_path: str) -> None:
        """Streams a dictionary as formatted JSON directly to target."""
        try:
            logger.info(f"STATUS - Uploading JSON to ADLS Gen2: {blob_path}")
            blob_client = self.container_client.get_blob_client(blob_path)
            json_data = json.dumps(data, ensure_ascii=False, indent=4)
            
            blob_client.upload_blob(json_data, overwrite=True)
            logger.info(f"SUCCES - Written blob to ADLS Gen2: {blob_path}")
        except Exception as e:
            logger.error(f"ERROR - Azure ADLS Gen2 Storage failure for path {blob_path}: {e}")
            raise


class INGESTIONPIPELINE:
    """The orchestrator that brings the API-client and Azure-uploader together."""

    def __init__(self, start_season: int, end_season: int, api_client: F1CLIENT, uploader: ADLSUPLOADER):
        self.start_season = start_season
        self.end_season = end_season
        self.api_client = api_client
        self.uploader = uploader

    def run(self) -> None:
        """Start the entire ingestionprocess for the configured seasonrange."""
        logger.info("=== F1 Ingestion Pipeline Started ===")
        logger.info(f"Loadrange configured: {self.start_season} - {self.end_season}")
        
        for season in range(self.start_season, self.end_season + 1):
            try:
                data = self.api_client.fetch_season_results(season)
                blob_path = f"f1/results/season={season}/bronze_results_{season}.json"
                self.uploader.upload_json(data, blob_path)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"ERROR - API extraction failed for season {season}: {e}")
            except Exception as e:
                logger.error(f"ERROR - Pipeline processing broken for season {season}: {e}")
                
        logger.info("=== F1 Ingestion Pipeline Successfully Finished ===")


def main():
    start_season = int(os.getenv("START_SEASON", "2014"))
    end_season = int(os.getenv("END_SEASON", "2025"))
    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME", "samainafdap123987123")
    container_name = os.getenv("CONTAINER_NAME", "bronze")

    api_client = F1CLIENT()
    uploader = ADLSUPLOADER(storage_account_name, container_name)
    
    pipeline = INGESTIONPIPELINE(
        start_season=start_season,
        end_season=end_season,
        api_client=api_client,
        uploader=uploader
    )
    
    pipeline.run()


if __name__ == "__main__":
    main()