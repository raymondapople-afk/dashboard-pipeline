"""Read a raw client CSV and rename its columns to the standard schema."""
import pandas as pd

from pipeline.config import ClientConfig


def load_raw(path: str, config: ClientConfig) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin1", keep_default_na=False)

    missing = [c for c in config.raw_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Raw CSV is missing column(s) expected by config '{config.name}': {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    df = df.rename(columns=config.column_map)
    return df[list(config.column_map.values())]
