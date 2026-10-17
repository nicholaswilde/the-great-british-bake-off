"""SQLite export utility for The Great British Bake Off dataset.

Provides relational SQL querying across all 4 processed tables with enforced
foreign keys and optimized series indexes.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TABLES = [
    "seasons",
    "bakers",
    "episodes",
    "performances",
]

BAKER_ID_ALIASES = {
    "s01_edd": "s01_edward",
    "s02_jo": "s02_joanne",
    "s07_val": "s07_valerie",
    "s08_yan": "s08_chuenyan",
    "s12_jairzeno": "s12_jairzinho",
}

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS seasons (
        series_number INTEGER PRIMARY KEY,
        year INTEGER,
        winner TEXT,
        hosts TEXT,
        judges TEXT,
        network TEXT,
        pbs_season REAL,
        netflix_collection REAL,
        roku_season REAL,
        location TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bakers (
        baker_id TEXT PRIMARY KEY,
        series_number INTEGER NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        occupation TEXT,
        hometown TEXT,
        overall_placement REAL,
        image_url TEXT,
        latitude REAL,
        longitude REAL,
        country TEXT,
        county_region TEXT,
        FOREIGN KEY (series_number) REFERENCES seasons(series_number)
    );

    """,
    """
    CREATE TABLE IF NOT EXISTS episodes (
        episode_id TEXT PRIMARY KEY,
        series_number INTEGER NOT NULL,
        episode_number INTEGER NOT NULL,
        theme TEXT,
        air_date TEXT,
        signature_time_min REAL,
        technical_time_min REAL,
        showstopper_time_min REAL,
        FOREIGN KEY (series_number) REFERENCES seasons(series_number)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS performances (
        performance_id TEXT PRIMARY KEY,
        baker_id TEXT NOT NULL,
        episode_id TEXT NOT NULL,
        signature_dish TEXT,
        technical_rank REAL,
        showstopper_dish TEXT,
        result TEXT NOT NULL,
        hollywood_handshake INTEGER NOT NULL DEFAULT 0,
        did_well INTEGER NOT NULL DEFAULT 0,
        at_risk INTEGER NOT NULL DEFAULT 0,
        absent INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (baker_id) REFERENCES bakers(baker_id),
        FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
    );
    """,
]

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_bakers_series ON bakers(series_number);",
    "CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes(series_number);",
    "CREATE INDEX IF NOT EXISTS idx_performances_baker ON performances(baker_id);",
    "CREATE INDEX IF NOT EXISTS idx_performances_episode ON performances(episode_id);",
]


class SQLiteExporter:
    """Exports processed GBBO datasets into a unified SQLite database with foreign keys."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        db_path: Path | str | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.db_path = Path(db_path) if db_path else self.processed_dir / "gbbo.db"

    def export(self) -> Path:
        """Export all processed tables into SQLite database with foreign keys and indexes."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(self.db_path)
        tables_exported = 0

        try:
            conn.execute("PRAGMA foreign_keys = ON;")

            # Initialize relational schema with foreign key constraints
            for stmt in SCHEMA_STATEMENTS:
                conn.execute(stmt)

            for table_name in TABLES:
                parquet_file = self.processed_dir / f"{table_name}.parquet"
                csv_file = self.processed_dir / f"{table_name}.csv"

                if parquet_file.exists():
                    df = pd.read_parquet(parquet_file)
                elif csv_file.exists():
                    df = pd.read_csv(csv_file)
                else:
                    logger.warning("No data file found for table '%s'", table_name)
                    continue

                if table_name == "performances":
                    # Reconcile any legacy baker aliases and convert boolean flags to 0/1 integers
                    if "baker_id" in df.columns:
                        df["baker_id"] = df["baker_id"].replace(BAKER_ID_ALIASES)
                    if "episode_id" in df.columns and "baker_id" in df.columns:
                        df["performance_id"] = df["episode_id"] + "_" + df["baker_id"]
                    for col in ["hollywood_handshake", "did_well", "at_risk", "absent"]:
                        if col in df.columns:
                            df[col] = df[col].astype(int)

                df.to_sql(table_name, conn, if_exists="append", index=False)
                tables_exported += 1
                logger.info(
                    "Exported %d rows into SQLite table '%s'", len(df), table_name
                )

            for idx_stmt in INDEX_STATEMENTS:
                conn.execute(idx_stmt)

            # Validate referential integrity
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_check;")
            fk_errors = cursor.fetchall()
            if fk_errors:
                raise RuntimeError(f"Foreign key integrity check failed: {fk_errors}")

            conn.commit()
            logger.info(
                "Successfully created SQLite database at %s with %d tables",
                self.db_path,
                tables_exported,
            )
        finally:
            conn.close()

        # Deterministic SQLite header version bytes normalization (offset 96-100)
        try:
            if self.db_path.exists():
                with open(self.db_path, "r+b") as f:
                    f.seek(96)
                    f.write(b"\x00\x2e\x8a\x14")
        except OSError as e:
            logger.warning("Could not normalize SQLite header: %s", e)

        return self.db_path


def export_to_sqlite(
    processed_dir: Path | str = "data/processed",
    db_path: Path | str | None = None,
) -> Path:
    """Helper function to run SQLite export."""
    exporter = SQLiteExporter(processed_dir=processed_dir, db_path=db_path)
    return exporter.export()
