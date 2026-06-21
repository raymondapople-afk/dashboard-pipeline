from pathlib import Path

from pipeline.clean import clean
from pipeline.config import load_client_config
from pipeline.ingest import load_raw

FIXTURE = Path(__file__).parent / "fixtures" / "sample_raw.csv"
HOTEL_FIXTURE = Path(__file__).parent / "fixtures" / "sample_hotel_raw.csv"


def _cleaned():
    config = load_client_config("uk_ecommerce")
    raw_df = load_raw(str(FIXTURE), config)
    return clean(raw_df, config), config


def _cleaned_hotel():
    config = load_client_config("hotel_bookings")
    raw_df = load_raw(str(HOTEL_FIXTURE), config)
    return clean(raw_df, config), config


def test_drops_exact_duplicates():
    df, _ = _cleaned()
    assert (df["order_id"] == "536365").sum() == 1


def test_drops_cancelled_orders():
    df, _ = _cleaned()
    assert not df["order_id"].str.startswith("C").any()


def test_drops_non_positive_quantity_and_price():
    df, _ = _cleaned()
    assert (df["quantity"] > 0).all()
    assert (df["unit_price"] > 0).all()


def test_fills_missing_customer_id_with_guest():
    df, _ = _cleaned()
    row = df[df["order_id"] == "536367"]
    assert row.iloc[0]["customer_id"] == "GUEST"


def test_drops_excluded_descriptions():
    df, _ = _cleaned()
    assert not df["order_id"].eq("536371").any()


def test_remaining_row_count():
    df, _ = _cleaned()
    assert len(df) == 4


def test_drop_duplicates_can_be_disabled_per_client():
    df, _ = _cleaned_hotel()
    assert (df["product_code"] == "A").sum() == 2  # duplicate pair both kept


def test_exclude_rows_drops_matching_rows():
    df, _ = _cleaned_hotel()
    assert not df["product_code"].eq("D").any()  # the is_canceled=1 booking


def test_hotel_remaining_row_count():
    df, _ = _cleaned_hotel()
    # 5 raw rows: 1 normal, 2 duplicate (kept), 1 canceled (dropped), 1
    # zero-nights (dropped by the existing quantity > 0 filter)
    assert len(df) == 3
