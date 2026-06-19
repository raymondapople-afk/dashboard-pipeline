"""Load and validate per-client pipeline configs."""
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "clients"

REQUIRED_STANDARD_FIELDS = {
    "order_id", "date", "customer_id", "country",
    "product_code", "product_desc", "quantity", "unit_price",
}


@dataclass
class CategoryRule:
    category: str
    keywords: list[str]


@dataclass
class ClientConfig:
    name: str
    column_map: dict[str, str]
    date_format: str
    cancellation_prefix: str
    category_rules: list[CategoryRule]
    excluded_descriptions: list[str]

    @property
    def raw_columns(self) -> list[str]:
        return list(self.column_map.keys())


def load_client_config(client: str) -> ClientConfig:
    path = CONFIG_DIR / f"{client}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No client config found at {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    column_map = raw["column_map"]
    standard_fields = set(column_map.values())
    missing = REQUIRED_STANDARD_FIELDS - standard_fields
    if missing:
        raise ValueError(
            f"Client config '{client}' is missing a mapping for required field(s): {missing}"
        )

    category_rules = [
        CategoryRule(category=r["category"], keywords=r["keywords"])
        for r in raw.get("category_rules", [])
    ]

    return ClientConfig(
        name=client,
        column_map=column_map,
        date_format=raw["date_format"],
        cancellation_prefix=raw["cancellation_prefix"],
        category_rules=category_rules,
        excluded_descriptions=raw.get("excluded_descriptions", []),
    )
