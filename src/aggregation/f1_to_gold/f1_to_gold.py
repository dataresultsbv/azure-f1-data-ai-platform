import os
import logging
import sys
import urllib.parse
import duckdb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)


class GoldAggregationConfig:
    """Manages pipeline configuration and environment variable loading."""
    def __init__(self):
        self.storage_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
        self.container_name = os.getenv("BLOB_CONTAINER_NAME", "")
        self.start_season = int(os.getenv("START_SEASON", "2014"))
        self.end_season = int(os.getenv("END_SEASON", "2025"))
        
        if not self.storage_url:
            logger.error("Missing mandatory environment variable: AZURE_STORAGE_ACCOUNT_URL")
            sys.exit(1)
            
        self.account_name = self._extract_account_name(self.storage_url)

    def _extract_account_name(self, url_string):
        """Extracts the storage account name from the full Azure Blob URL."""
        try:
            parsed_url = urllib.parse.urlparse(url_string)
            return parsed_url.netloc.split('.')[0]
        except Exception as e:
            logger.error(f"Failed to parse storage account name from URL '{url_string}': {e}")
            raise


class DuckDBCloudClient:
    """Handles initialization, extensions, and cloud security contexts for DuckDB."""
    def __init__(self, config: GoldAggregationConfig):
        self.config = config
        self.con = duckdb.connect(database=':memory:')
        self._initialize_extensions()
        self._authenticate()

    def _initialize_extensions(self):
        """Loads required core cloud drivers."""
        logger.info("Installing and loading DuckDB Azure extension...")
        self.con.execute("INSTALL azure; LOAD azure;")

    def _authenticate(self):
        """Sets up secure User-Assigned Managed Identity tracking for cloud paths."""
        logger.info(f"Configuring Managed Identity secret tracking for account: {self.config.account_name}")
        self.con.execute(f"""
            CREATE SECRET azure_identity (
                TYPE AZURE,
                PROVIDER CREDENTIAL_CHAIN,
                ACCOUNT_NAME '{self.config.account_name}'
            );
        """)

    def execute_query(self, query: str):
        """Executes a standard statement against the database session."""
        return self.con.execute(query)


class GoldAggregationEngine:
    """Orchestrates structural aggregations from partitioned Silver Parquet files to Gold."""
    def __init__(self, config: GoldAggregationConfig, client: DuckDBCloudClient):
        self.config = config
        self.client = client
        
        self.silver_race_results = f"az://{self.config.container_name}/silver/race_results/*/*.parquet"
        self.silver_driver_standings = f"az://{self.config.container_name}/silver/driver_standings/*/*.parquet"
        
        self.silver_drivers = f"az://{self.config.container_name}/silver/drivers/*.parquet"
        
        self.gold_destination = f"az://{self.config.container_name}/gold/driver_season_summary.parquet"

    def process(self):
        """Executes analytical logic and materializes the unified Gold dataset."""
        logger.info("Assembling analytical views and scanning partitioned paths...")
        
        aggregation_sql = f"""
            COPY (
                WITH season_driver_metrics AS (
                    SELECT
                        rr.season,
                        rr.driverId,
                        COUNT(*) AS races_entered,
                        SUM(CASE WHEN rr.positionOrder = 1 THEN 1 ELSE 0 END) AS wins,
                        SUM(CASE WHEN rr.positionOrder <= 3 THEN 1 ELSE 0 END) AS podiums,
                        SUM(CASE WHEN rr.fastest_lap_rank = 1 THEN 1 ELSE 0 END) AS fastest_laps,
                        SUM(rr.points) AS total_points,
                        ROUND(AVG(rr.positionOrder), 2) AS avg_finish_position,
                        ROUND(AVG(rr.grid), 2) AS avg_grid_position,
                        SUM(rr.grid - rr.positionOrder) AS positions_gained,
                        SUM(CASE WHEN rr.status <> 'Finished' THEN 1 ELSE 0 END) AS dnfs
                    FROM read_parquet('{self.silver_race_results}', hive_partitioning=1) rr
                    WHERE rr.season BETWEEN {self.config.start_season} AND {self.config.end_season}
                    GROUP BY rr.season, rr.driverId
                ),
                final_driver_standings AS (
                    SELECT
                        season,
                        driverId,
                        position AS championship_position,
                        points AS championship_points,
                        wins AS championship_wins
                    FROM (
                        SELECT *,
                               ROW_NUMBER() OVER (
                                   PARTITION BY season, driverId
                                   ORDER BY round DESC
                               ) AS rn
                        FROM read_parquet('{self.silver_driver_standings}', hive_partitioning=1)
                    )
                    WHERE rn = 1
                )
                SELECT 
                    m.*,
                    d.forename,
                    d.surname,
                    d.nationality,
                    s.championship_position,
                    s.championship_points,
                    s.championship_wins
                FROM season_driver_metrics m
                LEFT JOIN read_parquet('{self.silver_drivers}', hive_partitioning=1) d
                    ON m.driverId = d.driverId
                LEFT JOIN final_driver_standings s
                    ON m.season = s.season
                   AND m.driverId = s.driverId
                ORDER BY m.season DESC, s.championship_position ASC
            ) TO '{self.gold_destination}' (FORMAT 'PARQUET');
        """
        
        logger.info(f"Executing cloud transformations directly into target layer...")
        self.client.execute_query(aggregation_sql)
        logger.info(f"Gold table successfully generated and exported to: {self.gold_destination}")

if __name__ == "__main__":
    logger.info("Initializing Gold Medallion Platform Sequence...")
    try:
        config = GoldAggregationConfig()
        client = DuckDBCloudClient(config)
        engine = GoldAggregationEngine(config, client)
        
        engine.process()
        logger.info("Pipeline execution finalized successfully. Exiting clean.")
    except Exception as e:
        logger.critical(f"Unhandled orchestration crash encountered during processing: {e}")
        sys.exit(1)