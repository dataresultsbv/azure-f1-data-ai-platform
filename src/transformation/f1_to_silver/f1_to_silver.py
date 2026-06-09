import io
import logging
import os
import sys
from typing import List, Tuple

import polars as pl
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)


class F1Transformer:
    """
    Responsible for all Polars transformations from Bronze to Silver.
    """

    @staticmethod
    def extract_race_id_expr() -> pl.Expr:
        """
        Helper expression to generate a deterministic numeric raceId (Int32).
        """

        return (pl.col("season").cast(pl.Int32) * 100 + pl.col("round").cast(pl.Int32)).alias(
            "raceId"
        )

    def transform_results(
        self, json_bytes: bytes
    ) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
        """
        Parses results JSON into circuits, races, drivers, constructors, and race_results.
        """

        raw_df = pl.read_json(io.BytesIO(json_bytes))

        races_exploded = (
            raw_df.select(pl.col("MRData").struct.field("RaceTable").struct.field("Races"))
            .explode("Races")
            .unnest("Races")
        )

        races_with_id = races_exploded.with_columns(self.extract_race_id_expr())

        circuits = (
            races_with_id.select("Circuit")
            .unnest("Circuit")
            .select(
                [
                    pl.col("circuitId"),
                    pl.col("url"),
                    pl.col("circuitName").alias("name"),
                    pl.col("Location").struct.field("locality").alias("location"),
                    pl.col("Location").struct.field("country").alias("country"),
                    pl.col("Location").struct.field("lat").cast(pl.Float64).alias("lat"),
                    pl.col("Location").struct.field("long").cast(pl.Float64).alias("long"),
                ]
            )
        )

        races = races_with_id.select(
            [
                pl.col("raceId"),
                pl.col("season").cast(pl.Int32),
                pl.col("round").cast(pl.Int32),
                pl.col("Circuit").struct.field("circuitId").alias("circuitId"),
                pl.col("raceName").alias("name"),
                pl.col("date"),
                pl.col("time"),
                pl.col("url"),
            ]
        )

        results_exploded = (
            races_with_id.select(["raceId", "season", "Results"])
            .explode("Results")
            .unnest("Results")
            # Generate positionOrder dynamically based on entry order per race
            .with_columns(pl.int_range(1, pl.len() + 1).over("raceId").alias("positionOrder"))
        )

        drivers = (
            results_exploded.select("Driver")
            .unnest("Driver")
            .select(
                [
                    pl.col("driverId"),
                    pl.col("code"),
                    pl.col("permanentNumber").cast(pl.Int32, strict=False).alias("number"),
                    pl.col("givenName").alias("forename"),
                    pl.col("familyName").alias("surname"),
                    pl.col("dateOfBirth").alias("dob"),
                    pl.col("nationality"),
                    pl.col("url"),
                ]
            )
        )

        constructors = (
            results_exploded.select("Constructor")
            .unnest("Constructor")
            .select([pl.col("constructorId"), pl.col("name"), pl.col("nationality"), pl.col("url")])
        )

        race_results = results_exploded.select(
            [
                pl.col("raceId"),
                pl.col("season").cast(pl.Int32),
                pl.col("Driver").struct.field("driverId").alias("driverId"),
                pl.col("Constructor").struct.field("constructorId").alias("constructorId"),
                pl.col("number").cast(pl.Int32, strict=False),
                pl.col("grid").cast(pl.Int32),
                pl.col("position").cast(pl.Int32, strict=False),
                pl.col("positionText"),
                pl.col("positionOrder").cast(pl.Int32),
                pl.col("points").cast(pl.Float64),
                pl.col("laps").cast(pl.Int32),
                pl.col("status"),
                pl.col("FastestLap")
                .struct.field("rank")
                .cast(pl.Int32, strict=False)
                .alias("fastest_lap_rank"),
                pl.col("FastestLap")
                .struct.field("Time")
                .struct.field("time")
                .alias("fastest_lap_time"),
                pl.col("FastestLap")
                .struct.field("AverageSpeed")
                .struct.field("speed")
                .cast(pl.Float64, strict=False)
                .alias("fastest_lap_avgspeed"),
            ]
        )

        return circuits, races, drivers, constructors, race_results

    def transform_driver_standings(self, json_bytes: bytes) -> pl.DataFrame:
        """
        Parses driverStandings JSON into a clean relational table.
        """

        raw_df = pl.read_json(io.BytesIO(json_bytes))

        standings_exploded = (
            raw_df.select(
                pl.col("MRData").struct.field("StandingsTable").struct.field("StandingsLists")
            )
            .explode("StandingsLists")
            .select(
                [
                    pl.col("StandingsLists").struct.field("season").cast(pl.Int32).alias("season"),
                    pl.col("StandingsLists").struct.field("round").cast(pl.Int32).alias("round"),
                    pl.col("StandingsLists").struct.field("DriverStandings"),
                ]
            )
            .explode("DriverStandings")
            .unnest("DriverStandings")
        )

        return standings_exploded.select(
            [
                pl.col("season"),
                pl.col("round"),
                pl.col("Driver").struct.field("driverId").alias("driverId"),
                pl.col("points").cast(pl.Float64),
                pl.col("position").cast(pl.Int32),
                pl.col("positionText"),
                pl.col("wins").cast(pl.Int32),
            ]
        )

    def transform_constructor_standings(self, json_bytes: bytes) -> pl.DataFrame:
        """
        Parses constructorStandings JSON into a clean relational table.
        """

        raw_df = pl.read_json(io.BytesIO(json_bytes))

        standings_exploded = (
            raw_df.select(
                pl.col("MRData").struct.field("StandingsTable").struct.field("StandingsLists")
            )
            .explode("StandingsLists")
            .select(
                [
                    pl.col("StandingsLists").struct.field("season").cast(pl.Int32).alias("season"),
                    pl.col("StandingsLists").struct.field("round").cast(pl.Int32).alias("round"),
                    pl.col("StandingsLists").struct.field("ConstructorStandings"),
                ]
            )
            .explode("ConstructorStandings")
            .unnest("ConstructorStandings")
        )

        return standings_exploded.select(
            [
                pl.col("season"),
                pl.col("round"),
                pl.col("Constructor").struct.field("constructorId").alias("constructorId"),
                pl.col("points").cast(pl.Float64),
                pl.col("position").cast(pl.Int32),
                pl.col("positionText"),
                pl.col("wins").cast(pl.Int32),
            ]
        )


class F1StorageHandler:
    """
    Responsible for all READ/WRITE operations to and from Azure Data Lake containers.
    """

    def __init__(self, account_url: str):
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(account_url, credential=self.credential)
        self.bronze_client = self.blob_service_client.get_container_client("bronze")
        self.silver_client = self.blob_service_client.get_container_client("silver")

    def read_bronze_blob(self, blob_path: str) -> bytes:
        """
        Downloads a specific JSON from Bronze as a byte stream.
        """

        logger.info(f"STATUS - Downloading from Bronze: {blob_path}")
        blob_client = self.bronze_client.get_blob_client(blob_path)
        return blob_client.download_blob().readall()

    def write_silver_partitioned(self, df: pl.DataFrame, table_name: str, season: int) -> None:
        """
        Writes non-duplicate data to a specific Hive partition folder in the silver container.
        """

        blob_path = f"{table_name}/season={season}/data.parquet"
        logger.info(f"STATUS - Writing partitioned data to Silver: {blob_path}")
        self._upload_to_silver(df, blob_path)

    def write_silver_unpartitioned(self, df: pl.DataFrame, table_name: str) -> None:
        """
        Writes the deduplicated data to the tables directly at the root level.
        """

        blob_path = f"{table_name}/full.parquet"
        logger.info(f"STATUS - Overwriting table in Silver: {blob_path}")
        self._upload_to_silver(df, blob_path)

    def _upload_to_silver(self, df: pl.DataFrame, blob_path: str) -> None:
        """
        Internal helper to stream a Polars DataFrame as Parquet to Azure.
        """

        buffer = io.BytesIO()
        df.write_parquet(buffer)
        buffer.seek(0)
        blob_client = self.silver_client.get_blob_client(blob_path)
        blob_client.upload_blob(buffer.read(), overwrite=True)


class F1Orchestrator:
    """
    The orchestrator linking the storage handler and transformations into a single pipeline run.
    """

    def __init__(
        self, seasons: List[int], storage_handler: F1StorageHandler, transformer: F1Transformer
    ):
        self.seasons = seasons
        self.storage = storage_handler
        self.transformer = transformer

    def run(self) -> None:
        logger.info(f"STATUS - Starting Silver Full-Load Pipeline for seasons: {self.seasons}")

        batch_circuits: List[pl.DataFrame] = []
        batch_drivers: List[pl.DataFrame] = []
        batch_constructors: List[pl.DataFrame] = []

        for season in self.seasons:
            logger.info(f"STATUS - Processing Season {season}...")

            try:
                results_bytes = self.storage.read_bronze_blob(
                    f"f1/results/season={season}/bronze_results_{season}.json"
                )
                circuits, races, drivers, constructors, race_results = (
                    self.transformer.transform_results(results_bytes)
                )

                self.storage.write_silver_partitioned(races, "races", season)
                self.storage.write_silver_partitioned(race_results, "race_results", season)

                batch_circuits.append(circuits)
                batch_drivers.append(drivers)
                batch_constructors.append(constructors)
            except Exception as e:
                logger.error(f"ERROR - Failed processing results for season {season}: {e}")

            try:
                ds_bytes = self.storage.read_bronze_blob(
                    f"f1/driver_standings/season={season}/bronze_driver_standings_{season}.json"
                )
                driver_standings = self.transformer.transform_driver_standings(ds_bytes)
                self.storage.write_silver_partitioned(driver_standings, "driver_standings", season)
            except Exception as e:
                logger.error(f"ERROR - Failed processing driver standings for season {season}: {e}")

            try:
                cs_bytes = self.storage.read_bronze_blob(
                    f"f1/constructor_standings/season={season}/bronze_constructor_standings_{season}.json"
                )
                constructor_standings = self.transformer.transform_constructor_standings(cs_bytes)
                self.storage.write_silver_partitioned(
                    constructor_standings, "constructor_standings", season
                )
            except Exception as e:
                logger.error(
                    f"ERROR - Failed processing constructor standings for season {season}: {e}"
                )

            logger.info(f"SUCCESS - Successfully processed season {season}.")

        if batch_circuits and batch_drivers and batch_constructors:
            logger.info("STATUS - Deduplicate and write driver, constructor and circuit data.")

            final_circuits = pl.concat(batch_circuits).unique(subset=["circuitId"])
            final_drivers = pl.concat(batch_drivers).unique(subset=["driverId"])
            final_constructors = pl.concat(batch_constructors).unique(subset=["constructorId"])

            self.storage.write_silver_unpartitioned(final_circuits, "circuits")
            self.storage.write_silver_unpartitioned(final_drivers, "drivers")
            self.storage.write_silver_unpartitioned(final_constructors, "constructors")

        logger.info("SUCCES - Successfully completed Silver Transformation Pipeline.")


if __name__ == "__main__":
    STORAGE_ACCOUNT_URL = os.environ["AZURE_STORAGE_ACCOUNT_URL"]
    START_SEASON = int(os.getenv("START_SEASON", "2014"))
    END_SEASON = int(os.getenv("END_SEASON", "2025"))

    seasons_to_process = list(range(START_SEASON, END_SEASON + 1))

    handler = F1StorageHandler(account_url=STORAGE_ACCOUNT_URL)
    transformer = F1Transformer()

    pipeline = F1Orchestrator(
        seasons=seasons_to_process, storage_handler=handler, transformer=transformer
    )
    pipeline.run()
