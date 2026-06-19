"""Derive standard-schema fields (revenue, category) from cleaned data."""
import re

import pandas as pd

from pipeline.config import ClientConfig

STANDARD_COLUMNS = [
    "order_id", "date", "customer_id", "country", "product_code",
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
    df["category"] = df["product_desc"].apply(lambda d: _categorize(d, config))
    return df[STANDARD_COLUMNS]
