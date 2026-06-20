"""Generic, config-driven cleaning rules. Operates only on standard field
names, so this code does not change between clients."""
import pandas as pd

from pipeline.config import ClientConfig

TEXT_COLUMNS = ["order_id", "customer_id", "country", "product_code", "product_desc"]


def clean(df: pd.DataFrame, config: ClientConfig) -> pd.DataFrame:
    df = df.copy()

    for col in TEXT_COLUMNS:
        df[col] = df[col].str.strip()

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    # Keep full datetime precision here -- transform.py splits this into a
    # date and an hour-of-day field. Truncating to date here would lose the
    # time-of-day information needed for traffic/shopping-pattern analysis.
    df["date"] = pd.to_datetime(df["date"], format=config.date_format, errors="coerce")

    df = df.drop_duplicates()

    df = df[~df["order_id"].str.startswith(config.cancellation_prefix, na=False)]
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]
    df = df[~(df["product_desc"].eq("") & df["product_code"].eq(""))]
    df = df[df["date"].notna()]

    excluded = {d.lower() for d in config.excluded_descriptions}
    df = df[~df["product_desc"].str.lower().isin(excluded)]

    df["customer_id"] = df["customer_id"].replace("", "GUEST")

    return df.reset_index(drop=True)
