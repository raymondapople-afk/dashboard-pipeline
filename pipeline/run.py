"""CLI entrypoint: ingest -> clean -> transform -> export.

Usage:
    python -m pipeline.run --client uk_ecommerce --input data/raw/UK_E_Commerce_data.csv
"""
import argparse

from pipeline.clean import clean
from pipeline.config import load_client_config
from pipeline.export_csv import write_clean_csv
from pipeline.export_json import write_all
from pipeline.ingest import load_raw
from pipeline.transform import transform


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the client data pipeline.")
    parser.add_argument("--client", required=True, help="Client config name (config/clients/<client>.yaml)")
    parser.add_argument("--input", required=True, help="Path to the raw client CSV")
    parser.add_argument("--csv-out", default=None, help="Output path for cleaned CSV (default: data/processed/<client>_clean.csv)")
    parser.add_argument("--json-out-dir", default=None, help="Output dir for dashboard JSON (default: data/exports)")
    args = parser.parse_args()

    csv_out = args.csv_out or f"data/processed/{args.client}_clean.csv"
    json_out_dir = args.json_out_dir or "data/exports"

    config = load_client_config(args.client)

    raw_df = load_raw(args.input, config)
    raw_count = len(raw_df)

    cleaned_df = clean(raw_df, config)
    clean_count = len(cleaned_df)

    final_df = transform(cleaned_df, config)

    write_clean_csv(final_df, csv_out)
    write_all(final_df, json_out_dir)

    dropped = raw_count - clean_count
    total_revenue = final_df["revenue"].sum()
    date_min, date_max = final_df["date"].min(), final_df["date"].max()

    print(f"Client: {config.name}")
    print(f"Raw rows: {raw_count}")
    print(f"Cleaned rows: {clean_count} (dropped {dropped}, {dropped / raw_count:.1%})")
    print(f"Date range: {date_min} to {date_max}")
    print(f"Total revenue: {total_revenue:,.2f}")
    print(f"Wrote cleaned CSV: {csv_out}")
    print(f"Wrote dashboard JSON to: {json_out_dir}/")


if __name__ == "__main__":
    main()
