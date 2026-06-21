from pathlib import Path

from pipeline.clean import clean
from pipeline.config import load_client_config
from pipeline.ingest import load_raw
from pipeline.transform import transform

FIXTURE = Path(__file__).parent / "fixtures" / "sample_raw.csv"
COFFEE_FIXTURE = Path(__file__).parent / "fixtures" / "sample_coffee_raw.csv"
HOTEL_FIXTURE = Path(__file__).parent / "fixtures" / "sample_hotel_raw.csv"


def _transformed():
    config = load_client_config("uk_ecommerce")
    raw_df = load_raw(str(FIXTURE), config)
    cleaned_df = clean(raw_df, config)
    return transform(cleaned_df, config)


def _transformed_coffee():
    config = load_client_config("coffee_shop")
    raw_df = load_raw(str(COFFEE_FIXTURE), config)
    cleaned_df = clean(raw_df, config)
    return transform(cleaned_df, config)


def _transformed_hotel():
    config = load_client_config("hotel_bookings")
    raw_df = load_raw(str(HOTEL_FIXTURE), config)
    cleaned_df = clean(raw_df, config)
    return transform(cleaned_df, config)


def test_revenue_is_quantity_times_unit_price():
    df = _transformed()
    row = df[df["order_id"] == "536370"].iloc[0]
    assert row["revenue"] == 8 * 2.75


def test_category_keyword_match():
    df = _transformed()
    row = df[df["order_id"] == "536366"].iloc[0]
    assert row["category"] == "Home Decor"  # matched on "lantern"


def test_category_falls_back_to_uncategorized():
    df = _transformed()
    row = df[df["order_id"] == "536370"].iloc[0]
    assert row["category"] == "Uncategorized"  # "novelty item" matches no rule


def test_hour_and_date_split_from_timestamp():
    df = _transformed()
    row = df[df["order_id"] == "536366"].iloc[0]  # raw timestamp 12/1/2010 8:28
    assert row["hour"] == 8
    assert str(row["date"]) == "2010-12-01"


def test_real_category_column_is_not_overwritten_by_keyword_rules():
    df = _transformed_coffee()
    row = df[df["order_id"] == "2"].iloc[0]  # product_category "Tea"
    assert row["category"] == "Tea"  # would be "Uncategorized" if keyword-derived


def test_coffee_hour_combines_separate_date_and_time_columns():
    df = _transformed_coffee()
    row = df[df["order_id"] == "3"].iloc[0]  # raw transaction_time 13:14:04
    assert row["hour"] == 13
    assert str(row["date"]) == "2023-01-02"


def test_hotel_revenue_is_adr_times_total_nights():
    # transform.py needed no changes for this -- revenue = quantity * unit_price
    # already equals adr * nights once ingest.py derives quantity correctly.
    df = _transformed_hotel()
    row = df[df["product_code"] == "C"].iloc[0]  # adr=100, nights=0+3=3
    assert row["quantity"] == 3
    assert row["unit_price"] == 100
    assert row["revenue"] == 300


def test_hotel_category_passes_through_market_segment():
    df = _transformed_hotel()
    row = df[df["product_code"] == "C"].iloc[0]
    assert row["category"] == "Direct"


def test_hotel_hour_is_zero_with_no_time_of_day_data():
    df = _transformed_hotel()
    row = df[df["product_code"] == "C"].iloc[0]
    assert row["hour"] == 0
