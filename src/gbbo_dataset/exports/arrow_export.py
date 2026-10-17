"""Apache Arrow IPC and Parquet exporter for The Great British Bake Off dataset.

Provides columnar compression and Arrow IPC streaming for high-throughput
analytics and AI/ML model pipelines.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
from pyarrow import feather

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


class ArrowExporter:
    """Exports processed GBBO tables to Apache Arrow IPC format and Parquet files."""

    def __init__(
        self,
        processed_dir: Path | str = "data/processed",
        arrow_dir: Path | str | None = None,
    ) -> None:
        self.processed_dir = Path(processed_dir)
        self.arrow_dir = Path(arrow_dir) if arrow_dir else self.processed_dir / "arrow"

    def load_table(self, table_name: str) -> pd.DataFrame:
        """Load a table from parquet or csv with legacy alias normalization."""
        parquet_path = self.processed_dir / f"{table_name}.parquet"
        csv_path = self.processed_dir / f"{table_name}.csv"

        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(
                f"Table '{table_name}' not found in {self.processed_dir} (.parquet or .csv)"
            )

        if table_name == "performances":
            if "baker_id" in df.columns:
                df["baker_id"] = df["baker_id"].replace(BAKER_ID_ALIASES)
            if "episode_id" in df.columns and "baker_id" in df.columns:
                df["performance_id"] = df["episode_id"] + "_" + df["baker_id"]

        return df

    def export_parquet_tables(self) -> dict[str, Path]:
        """Export all processed tables into standalone Parquet (.parquet) files in processed_dir."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        exported: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)
            output_file = self.processed_dir / f"{table_name}.parquet"
            df.to_parquet(output_file, index=False)
            exported[table_name] = output_file
            logger.info(
                "Exported %s to Parquet (%d rows) -> %s",
                table_name,
                len(df),
                output_file,
            )

        return exported

    def export_arrow_tables(self) -> dict[str, Path]:
        """Export all processed tables into Apache Arrow IPC (.arrow) stream files."""
        self.arrow_dir.mkdir(parents=True, exist_ok=True)
        exported: dict[str, Path] = {}

        for table_name in TABLES:
            df = self.load_table(table_name)
            arrow_table = pa.Table.from_pandas(df, preserve_index=False)
            output_file = self.arrow_dir / f"{table_name}.arrow"
            feather.write_feather(arrow_table, output_file, compression="zstd")
            exported[table_name] = output_file
            logger.info(
                "Exported %s to Arrow IPC (%d rows) -> %s",
                table_name,
                len(df),
                output_file,
            )

        return exported

    def export_all(self) -> dict[str, dict[str, Path]]:
        """Export both Parquet and Arrow IPC files."""
        parquet_files = self.export_parquet_tables()
        arrow_files = self.export_arrow_tables()
        return {
            "parquet": parquet_files,
            "arrow": arrow_files,
        }


def export_arrow(
    processed_dir: Path | str = "data/processed",
    arrow_dir: Path | str | None = None,
) -> dict[str, dict[str, Path]]:
    """Helper function to run Arrow and Parquet exports."""
    exporter = ArrowExporter(processed_dir=processed_dir, arrow_dir=arrow_dir)
    return exporter.export_all()
