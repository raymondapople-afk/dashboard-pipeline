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
    encoding: str
    constants: dict[str, str]
    date_columns: list[str]
    drop_duplicates: bool
    exclude_rows: list[dict]
    sum_columns: dict[str, list[str]]
    synthesize_order_id: bool

    @property
    def raw_columns(self) -> list[str]:
        columns = list(self.column_map.keys())
        if self.date_columns:
            columns += self.date_columns
        for sources in self.sum_columns.values():
            columns += sources
        return columns


def load_client_config(client: str) -> ClientConfig:
    path = CONFIG_DIR / f"{client}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No client config found at {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    column_map = raw["column_map"]
    constants = raw.get("constants", {})
    date_columns = raw.get("date_columns", [])
    sum_columns = raw.get("sum_columns", {})
    synthesize_order_id = raw.get("synthesize_order_id", False)

    standard_fields = set(column_map.values()) | set(constants.keys()) | set(sum_columns.keys())
    if date_columns:
        standard_fields.add("date")
    if synthesize_order_id:
        standard_fields.add("order_id")
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
        encoding=raw.get("encoding", "utf-8-sig"),
        constants=constants,
        date_columns=date_columns,
        drop_duplicates=raw.get("drop_duplicates", True),
        exclude_rows=raw.get("exclude_rows", []),
        sum_columns=sum_columns,
        synthesize_order_id=synthesize_order_id,
    )
