from pathlib import Path

from pipeline.clean import clean
from pipeline.config import load_client_config
from pipeline.ingest import load_raw
from pipeline.transform import transform

FIXTURE = Path(__file__).parent / "fixtures" / "sample_raw.csv"


def _transformed():
    config = load_client_config("uk_ecommerce")
    raw_df = load_raw(str(FIXTURE), config)
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
