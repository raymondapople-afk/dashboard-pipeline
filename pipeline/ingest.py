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

    # Some clients (e.g. bookings data) record a quantity as the sum of two
    # raw columns (weekend nights + week nights) rather than one column.
    for target, sources in config.sum_columns.items():
        df[target] = sum(pd.to_numeric(df[s], errors="coerce") for s in sources)

    df = df.rename(columns=config.column_map)

    standard_columns = list(config.column_map.values())
    if config.date_columns:
        standard_columns.append("date")
    standard_columns += list(config.sum_columns.keys())

    # Some clients have no raw column for a required standard field at all
    # (e.g. anonymous POS data has no customer_id, single-country exports
    # have no country column) -- fill those in as literal constants.
    for field, value in config.constants.items():
        df[field] = value
        standard_columns.append(field)

    # Some clients have no primary key column at all -- synthesize one from
    # row position so downstream order-counting (nunique(order_id)) still
    # works rather than every row sharing one constant ID.
    if config.synthesize_order_id:
        df["order_id"] = (df.index + 1).astype(str)
        standard_columns.append("order_id")

    # Retain any extra raw column referenced by exclude_rows even though it's
    # not part of the standard schema -- clean.py needs it to filter rows;
    # transform.py's final column selection drops it afterward.
    extra_columns = [r["column"] for r in config.exclude_rows if r["column"] not in standard_columns]

    return df[standard_columns + extra_columns]
