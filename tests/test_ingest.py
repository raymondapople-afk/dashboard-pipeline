from pathlib import Path

from pipeline.config import load_client_config
from pipeline.ingest import load_raw

FIXTURE = Path(__file__).parent / "fixtures" / "sample_coffee_raw.csv"


def _loaded():
    config = load_client_config("coffee_shop")
    return load_raw(str(FIXTURE), config), config


def test_combines_date_and_time_columns():
    df, _ = _loaded()
    row = df[df["order_id"] == "1"].iloc[0]
    assert row["date"] == "01/01/2023 07:06:11"


def test_fills_constants_for_missing_columns():
    df, _ = _loaded()
    assert (df["customer_id"] == "GUEST").all()
    assert (df["country"] == "USA").all()


def test_passes_through_real_category_column():
    df, _ = _loaded()
    row = df[df["order_id"] == "1"].iloc[0]
    assert row["category"] == "Coffee"
