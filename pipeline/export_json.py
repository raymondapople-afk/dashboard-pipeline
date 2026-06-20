"""Pre-aggregate the cleaned data into small, chart-ready JSON files for the
standalone web dashboard."""
import json
from pathlib import Path

import pandas as pd


def _write_json(data, out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def write_revenue_by_date(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby("date")["revenue"].sum().round(2).reset_index()
    agg = agg.sort_values("date")
    _write_json(agg.to_dict(orient="records"), out_path)


def write_revenue_by_category(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby("category")["revenue"].sum().round(2).reset_index()
    agg = agg.sort_values("revenue", ascending=False)
    _write_json(agg.to_dict(orient="records"), out_path)


def write_orders_by_hour(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby("hour").agg(
        order_count=("order_id", "nunique"),
        revenue=("revenue", "sum"),
    )
    agg = agg.reindex(range(24), fill_value=0).reset_index()
    agg["revenue"] = agg["revenue"].round(2)
    _write_json(agg.to_dict(orient="records"), out_path)


def write_orders_by_hour_country(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby(["hour", "country"]).agg(
        order_count=("order_id", "nunique"),
        revenue=("revenue", "sum"),
    ).reset_index()
    agg["revenue"] = agg["revenue"].round(2)
    agg = agg.sort_values(["hour", "country"])
    _write_json(agg.to_dict(orient="records"), out_path)


def write_revenue_by_hour_category(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby(["hour", "category"]).agg(
        revenue=("revenue", "sum"),
        item_count=("order_id", "size"),
    ).reset_index()
    agg["revenue"] = agg["revenue"].round(2)
    agg = agg.sort_values(["hour", "category"])
    _write_json(agg.to_dict(orient="records"), out_path)


def write_customer_trends(df: pd.DataFrame, out_path: str) -> None:
    agg = df.groupby("customer_id").agg(
        order_count=("order_id", "nunique"),
        total_revenue=("revenue", "sum"),
        first_order_date=("date", "min"),
        last_order_date=("date", "max"),
    ).reset_index()
    agg["total_revenue"] = agg["total_revenue"].round(2)
    agg = agg.sort_values("total_revenue", ascending=False)
    _write_json(agg.to_dict(orient="records"), out_path)


def write_all(df: pd.DataFrame, out_dir: str) -> None:
    out_dir = Path(out_dir)
    write_revenue_by_date(df, out_dir / "revenue_by_date.json")
    write_revenue_by_category(df, out_dir / "revenue_by_category.json")
    write_customer_trends(df, out_dir / "customer_trends.json")
    write_orders_by_hour(df, out_dir / "orders_by_hour.json")
    write_orders_by_hour_country(df, out_dir / "orders_by_hour_country.json")
    write_revenue_by_hour_category(df, out_dir / "revenue_by_hour_category.json")
