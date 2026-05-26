import argparse
import re
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from schemas.OpenBCIProcesorSchema import OpenBCIProcessorConfig

        
class OpenBCIProcessor:
    def __init__(self, config: OpenBCIProcessorConfig):
        self.config = config
        self.metadata: Dict[str, Optional[str]] = {
            "number_of_channels": None,
            "sample_rate_hz": None,
            "board": None,
        }

    def read_metadata(self) -> Dict[str, Optional[str]]:
        with open(
            self.config.input_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:
            for line in file:
                line = line.strip()

                if not line.startswith("%"):
                    break

                if "Number of channels" in line:
                    match = re.search(r"=\s*(\d+)", line)
                    if match:
                        self.metadata["number_of_channels"] = int(match.group(1))

                elif "Sample Rate" in line:
                    match = re.search(r"=\s*([\d.]+)", line)
                    if match:
                        self.metadata["sample_rate_hz"] = float(match.group(1))

                elif "Board" in line:
                    self.metadata["board"] = line.split("=", 1)[-1].strip()

        return self.metadata

    def load_file(self) -> pd.DataFrame:
        df = pd.read_csv(
            self.config.input_path,
            comment="%",
            skipinitialspace=True
        )

        df.columns = [col.strip() for col in df.columns]

        return df

    @staticmethod
    def sort_channel_columns(columns, prefix: str):
        def extract_index(col):
            match = re.search(rf"{re.escape(prefix)}\s*(\d+)", col)
            return int(match.group(1)) if match else 9999

        return sorted(
            [col for col in columns if col.startswith(prefix)],
            key=extract_index
        )

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        exg_cols = self.sort_channel_columns(df.columns, "EXG Channel")
        accel_cols = self.sort_channel_columns(df.columns, "Accel Channel")

        selected_cols = []

        if "Sample Index" in df.columns:
            selected_cols.append("Sample Index")

        selected_cols.extend(exg_cols)
        selected_cols.extend(accel_cols)

        optional_cols = [
            "Timestamp",
            "Marker Channel",
            "Timestamp (Formatted)",
        ]

        for col in optional_cols:
            if col in df.columns:
                selected_cols.append(col)

        clean_df = df[selected_cols].copy()

        rename_map = {}

        if "Sample Index" in clean_df.columns:
            rename_map["Sample Index"] = "sample_index"

        for col in exg_cols:
            idx = re.search(r"EXG Channel\s*(\d+)", col).group(1)
            rename_map[col] = f"exg_{idx}"

        for col in accel_cols:
            idx = re.search(r"Accel Channel\s*(\d+)", col).group(1)
            rename_map[col] = f"accel_{idx}"

        if "Timestamp" in clean_df.columns:
            rename_map["Timestamp"] = "timestamp_unix"

        if "Marker Channel" in clean_df.columns:
            rename_map["Marker Channel"] = "marker"

        if "Timestamp (Formatted)" in clean_df.columns:
            rename_map["Timestamp (Formatted)"] = "timestamp_formatted"

        clean_df = clean_df.rename(columns=rename_map)

        numeric_cols = [
            col for col in clean_df.columns
            if col != "timestamp_formatted"
        ]

        for col in numeric_cols:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

        sample_rate = self.metadata.get("sample_rate_hz")

        if "sample_index" in clean_df.columns and sample_rate:
            clean_df.insert(
                1,
                "time_seconds",
                clean_df["sample_index"] / sample_rate
            )

        elif "timestamp_unix" in clean_df.columns:
            clean_df.insert(
                1,
                "time_seconds",
                clean_df["timestamp_unix"] - clean_df["timestamp_unix"].iloc[0]
            )

        return clean_df

    def print_summary(self, clean_df: pd.DataFrame) -> None:
        print("\n=== Resumo do arquivo OpenBCI ===")
        print(f"Board: {self.metadata.get('board')}")
        print(f"Número de canais informado: {self.metadata.get('number_of_channels')}")
        print(f"Sample rate: {self.metadata.get('sample_rate_hz')} Hz")

        print(f"\nNúmero de amostras: {len(clean_df)}")

        if "time_seconds" in clean_df.columns and len(clean_df) > 0:
            duration = clean_df["time_seconds"].iloc[-1] - clean_df["time_seconds"].iloc[0]
            print(f"Duração aproximada: {duration:.3f} segundos")

        exg_cols = [col for col in clean_df.columns if col.startswith("exg_")]

        if exg_cols:
            print("\nEstatísticas dos canais EXG:")
            stats = clean_df[exg_cols].describe().loc[["mean", "std", "min", "max"]]
            print(stats)

    def process(self, data) -> pd.DataFrame:

        self.config = data
        self.read_metadata()

        raw_df = self.load_file()
        clean_df = self.clean_dataframe(raw_df)

        output_path = Path(self.config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        clean_df.to_csv(output_path, index=False)

        self.print_summary(clean_df)

        print(f"\nCSV salvo em: {output_path}")

        return clean_df