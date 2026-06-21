"""Read a raw client CSV and rename its columns to the standard schema."""
import pandas as pd

from pipeline.config import ClientConfig


def load_raw(path: str, config: ClientConfig) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding=config.encoding, keep_default_na=False)

    missing = [c for c in config.raw_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Raw CSV is missing column(s) expected by config '{config.name}': {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    # Some clients log date and time-of-day as separate raw columns instead of
    # one combined timestamp -- join them before the standard rename so
    # downstream cleaning only ever has to parse a single "date" field.
    if config.date_columns:
        df["date"] = df[config.date_columns].agg(" ".join, axis=1)

    df = df.rename(columns=config.column_map)

    standard_columns = list(config.column_map.values())
    if config.date_columns:
        standard_columns.append("date")

    # Some clients have no raw column for a required standard field at all
    # (e.g. anonymous POS data has no customer_id, single-country exports
    # have no country column) -- fill those in as literal constants.
    for field, value in config.constants.items():
        df[field] = value
        standard_columns.append(field)

    return df[standard_columns]
