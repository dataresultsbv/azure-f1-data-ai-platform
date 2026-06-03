import os
import json
import logging
import sys
import time
import requests
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)

class F1CLIENT:
    """Responsible for communication with the jolpica-f1-api with auto-pagination and rate-limiting resilience."""
    
    BASE_URL = "https://api.jolpi.ca/ergast/f1"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = self._initialize_session()

    def _initialize_session(self) -> requests.Session:
        """Configures a request session with a robust exponential backoff retry strategy."""
        session = requests.Session()
        
        # Configure retries to catch rate limits (429) and transient server hiccups
        retry_strategy = Retry(
            total=5,                        # Max number of retries before giving up
            backoff_factor=2,               # Delays: 2s, 4s, 8s, 16s... between retries
            status_forcelist=[429, 500, 502, 503, 504], # Status codes to trigger a retry
            raise_on_status=False           # Allows response.raise_for_status() to handle the final failure
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _merge_payloads(self, base_payload: Dict[str, Any], new_payload: Dict[str, Any]) -> None:
    """Intelligently merges nested data lists, blending split pages for identical race rounds."""
    base_mr = base_payload.get("MRData", {})
    new_mr = new_payload.get("MRData", {})
    
    if "RaceTable" in base_mr and "RaceTable" in new_mr:
        base_races = base_mr["RaceTable"].get("Races", [])
        new_races = new_mr["RaceTable"].get("Races", [])
        
        for new_race in new_races:
            existing_race = next((r for r in base_races if r.get("round") == new_race.get("round")), None)
            
            if existing_race:
                existing_race.get("Results", []).extend(new_race.get("Results", []))
            else:
                base_races.append(new_race)
                
    elif "StandingsTable" in base_mr and "StandingsTable" in new_mr:
        base_lists = base_mr["StandingsTable"].get("StandingsLists", [])
        new_lists = new_mr["StandingsTable"].get("StandingsLists", [])
        if base_lists and new_lists:
            if "DriverStandings" in base_lists[0]:
                base_lists[0]["DriverStandings"].extend(new_lists[0].get("DriverStandings", []))
            elif "ConstructorStandings" in base_lists[0]:
                base_lists[0]["ConstructorStandings"].extend(new_lists[0].get("ConstructorStandings", []))

    def _fetch_data(self, endpoint_url: str) -> Dict[str, Any]:
        """Generic helper to handle API limit ceilings with built-in throttling."""
        limit = 100
        offset = 0
        combined_data = None
        
        while True:
            params = {"limit": limit, "offset": offset}
            
            # Using the adaptive session instead of generic requests.get
            response = self.session.get(endpoint_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            payload = response.json()
            mr_data = payload.get("MRData", {})
            total = int(mr_data.get("total", 0))
            
            if combined_data is None:
                combined_data = payload
            else:
                self._merge_payloads(combined_data, payload)
                
            offset += limit
            
            if offset >= total or total == 0:
                break
            
            # Be polite: Add a 1-second delay between successful page requests to respect the API gateway
            time.sleep(1.0)
                
        if combined_data and "MRData" in combined_data:
            combined_data["MRData"]["limit"] = offset
            
        return combined_data

    def fetch_season_results(self, season: int) -> Dict[str, Any]:
        """Retrieves race results for a specific season."""
        url = f"{self.BASE_URL}/{season}/results.json"
        logger.info(f"Connecting to API for race results season {season}")
        return self._fetch_data(url)

    def fetch_driver_standings(self, season: int) -> Dict[str, Any]:
        """Retrieves driver standings for a specific season."""
        url = f"{self.BASE_URL}/{season}/driverStandings.json"
        logger.info(f"Connecting to API for driver standings season {season}")
        return self._fetch_data(url)

    def fetch_constructor_standings(self, season: int) -> Dict[str, Any]:
        """Retrieves constructor standings for a specific season."""
        url = f"{self.BASE_URL}/{season}/constructorStandings.json"
        logger.info(f"Connecting to API for constructor standings season {season}")
        return self._fetch_data(url)


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
        """Start the entire ingestion process for the configured season range."""
        logger.info("F1 Ingestion Pipeline Started")
        logger.info(f"Loadrange configured: {self.start_season} - {self.end_season}")
        
        for season in range(self.start_season, self.end_season + 1):
            logger.info(f"--- Processing Season {season} ---")
            
            # 1. Race Results
            try:
                data = self.api_client.fetch_season_results(season)
                blob_path = f"f1/results/season={season}/bronze_results_{season}.json"
                self.uploader.upload_json(data, blob_path)
            except Exception as e:
                logger.error(f"ERROR - Race results failed for season {season}: {e}")

            # 2. Driver Standings
            try:
                data = self.api_client.fetch_driver_standings(season)
                blob_path = f"f1/driver_standings/season={season}/bronze_driver_standings_{season}.json"
                self.uploader.upload_json(data, blob_path)
            except Exception as e:
                logger.error(f"ERROR - Driver standings failed for season {season}: {e}")

            # 3. Constructor Standings
            try:
                data = self.api_client.fetch_constructor_standings(season)
                blob_path = f"f1/constructor_standings/season={season}/bronze_constructor_standings_{season}.json"
                self.uploader.upload_json(data, blob_path)
            except Exception as e:
                logger.error(f"ERROR - Constructor standings failed for season {season}: {e}")
                
        logger.info("F1 Ingestion Pipeline Successfully Finished")


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