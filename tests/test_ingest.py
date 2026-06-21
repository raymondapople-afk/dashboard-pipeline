from pathlib import Path

from pipeline.config import load_client_config
from pipeline.ingest import load_raw

FIXTURE = Path(__file__).parent / "fixtures" / "sample_coffee_raw.csv"
HOTEL_FIXTURE = Path(__file__).parent / "fixtures" / "sample_hotel_raw.csv"


def _loaded():
    config = load_client_config("coffee_shop")
    return load_raw(str(FIXTURE), config), config


def _loaded_hotel():
    config = load_client_config("hotel_bookings")
    return load_raw(str(HOTEL_FIXTURE), config), config


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


def test_sum_columns_produces_quantity_from_two_raw_columns():
    df, _ = _loaded_hotel()
    row = df[df["product_code"] == "C"].iloc[0]  # weekend=0, week=3 -> 3 nights
    assert row["quantity"] == 3


def test_synthesize_order_id_produces_unique_sequential_ids():
    df, _ = _loaded_hotel()
    assert df["order_id"].tolist() == ["1", "2", "3", "4", "5"]
    assert df["order_id"].is_unique


def test_combines_three_date_columns_with_month_name():
    df, _ = _loaded_hotel()
    row = df[df["product_code"] == "C"].iloc[0]
    assert row["date"] == "2015 July 1"
