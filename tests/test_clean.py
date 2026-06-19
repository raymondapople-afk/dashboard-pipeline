from pathlib import Path

from pipeline.clean import clean
from pipeline.config import load_client_config
from pipeline.ingest import load_raw

FIXTURE = Path(__file__).parent / "fixtures" / "sample_raw.csv"


def _cleaned():
    config = load_client_config("uk_ecommerce")
    raw_df = load_raw(str(FIXTURE), config)
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
