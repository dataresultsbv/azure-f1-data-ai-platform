import os
import json
import logging
import sys
import requests
from pathlib import Path

# Setup professionele logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.jolpi.ca/ergast/f1"

def ingest_season_results(season: int, base_dir: Path):
    url = f"{BASE_URL}/{season}/results.json"
    params = {"limit": 1000}
    
    logger.info(f"Connecting to API for season {season} -> {url}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        total_results = data.get("MRData", {}).get("total", 0)
        logger.info(f"Succes - HTTP {response.status_code} | Records: {total_results}")
        
        output_dir = base_dir / "bronze" / "f1" / "results" / f"season={season}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"raw_results_{season}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Succes - Written file to: {file_path}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"× ERROR - While reading/writing season {season}: {e}")

def main():
    logger.info("=== F1 Ingestion Pipeline Started ===")
    
    start_season = int(os.getenv("START_SEASON", "2014"))
    end_season = int(os.getenv("END_SEASON", "2025"))
    
    # Bepaal de hoofdmap voor de data-opslag.
    # Als DATA_DIR in de environment staat (zoals in Docker), gebruiken we die.
    # Zo niet (lokaal), dan pakken we de standaard `./data` map.
    env_data_dir = os.getenv("DATA_DIR")
    if env_data_dir:
        base_dir = Path(env_data_dir)
    else:
        # Veilige lokale fallback: zoekt naar 'data' in de huidige werkmap
        base_dir = Path.cwd() / "data"
    
    logger.info(f"Loadrange configured:{start_season} - {end_season}")
    logger.info(f"Ingesting into: {base_dir}")
    
    for season in range(start_season, end_season + 1):
        ingest_season_results(season, base_dir)
        
    logger.info("=== F1 Ingestion Pipeline Succesfully Finished ===")

if __name__ == "__main__":
    main()