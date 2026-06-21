"""Derive standard-schema fields (revenue, category) from cleaned data."""
import re

import pandas as pd

from pipeline.config import ClientConfig

STANDARD_COLUMNS = [
    "order_id", "date", "hour", "customer_id", "country", "product_code",
    "product_desc", "category", "quantity", "unit_price", "revenue",
]


def _categorize(description: str, config: ClientConfig) -> str:
    desc_lower = description.lower()
    for rule in config.category_rules:
        if any(re.search(rf"\b{re.escape(keyword)}(e?s)?\b", desc_lower) for keyword in rule.keywords):
            return rule.category
    return "Uncategorized"


def transform(df: pd.DataFrame, config: ClientConfig) -> pd.DataFrame:
    df = df.copy()
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)

    # If the client mapped a real category column via column_map, ingest.py
    # already populated it -- keep it as-is rather than overwriting it with
    # keyword derivation, which only makes sense when no real category exists.
    if "category" in df.columns:
        df["category"] = df["category"].str.strip()
    else:
        df["category"] = df["product_desc"].apply(lambda d: _categorize(d, config))

    df["hour"] = df["date"].dt.hour
    df["date"] = df["date"].dt.date
    return df[STANDARD_COLUMNS]
