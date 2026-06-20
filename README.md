# Dashboard Data Pipeline

Ingests a raw client CSV export, cleans it into a standard schema, and
produces:

1. A flat cleaned CSV (`data/processed/<client>_clean.csv`) to point Looker
   Studio at.
2. Pre-aggregated JSON files (`data/exports/*.json`) for a standalone web
   dashboard.

## Run it

```
pip install -r requirements.txt
python -m pipeline.run --client uk_ecommerce --input data/raw/UK_E_Commerce_data.csv
```

Outputs:
- `data/processed/uk_ecommerce_clean.csv` — line-item grain, standard schema
- `data/exports/revenue_by_date.json`
- `data/exports/revenue_by_category.json`
- `data/exports/customer_trends.json`
- `data/exports/orders_by_hour.json` — order count + revenue per hour-of-day (0–23), zero-filled
- `data/exports/orders_by_hour_country.json` — order count + revenue per hour-of-day x country
- `data/exports/revenue_by_hour_category.json` — revenue + line-item count per hour-of-day x category

The CLI also prints the single busiest order hour (`Peak order hour: HH:00`)
on every run.

## Standard schema

`order_id, date, hour, customer_id, country, product_code, product_desc, category, quantity, unit_price, revenue`

`hour` (0–23) and `date` are both split from the raw timestamp in
`transform.py` — `clean.py` deliberately keeps full datetime precision
through cleaning so this split can happen later. `hour` exists specifically
to support shopping/traffic-trend analysis (when orders are placed, broken
down by country or category) — it's not used for order or customer
identification, since `order_id` already groups an order's line items and
`customer_id` + distinct `order_id` count already identifies repeat
customers, regardless of time-of-day.

## Adding a new client

The cleaning/transform code (`pipeline/clean.py`, `pipeline/transform.py`)
never references a specific client's column names — it only knows the
standard schema above. To onboard a new client:

1. Drop their raw CSV in `data/raw/`.
2. Copy `config/clients/uk_ecommerce.yaml` to `config/clients/<new_client>.yaml`
   and edit:
   - `column_map` — map their raw column headers to the standard field names.
   - `date_format` — the `strptime` format of their date column.
   - `cancellation_prefix` — the order-id prefix that marks a cancelled order
     (set to something that will never match, e.g. `"__NONE__"`, if N/A).
   - `category_rules` — keyword → category buckets for their product catalog.
     Rules use word-boundary matching (`re.search(r"\bword\b", ...)`), not
     "first match wins" alphabetically — order rules from most to least
     specific. Unmatched products fall back to `"Uncategorized"`.
3. Run:
   ```
   python -m pipeline.run --client <new_client> --input data/raw/<their_file>.csv
   ```

No changes to `pipeline/*.py` should be needed unless the new client's data
has a genuinely new shape of data-quality problem (in which case, extend
`clean.py`'s rules — keep them config-driven where the rule varies by client).

## Notes on this dataset (UK Online Retail)

- Cancelled orders (`InvoiceNo` starting with `C`) and non-positive
  quantity/price rows (returns, free samples, adjustments) are dropped
  entirely — the cleaned data reflects completed sales only, no negative
  revenue.
- Rows with a missing `CustomerID` are kept and labeled `"GUEST"` rather
  than dropped (~25% of raw rows lack a customer id — dropping them would
  discard a large share of real revenue).
- This export has no real product category field, so `category` is derived
  from a starter set of keyword rules in `config/clients/uk_ecommerce.yaml`
  matched against `Description`. About half of line items don't match any
  rule and fall into `"Uncategorized"` — expand the keyword list as needed
  for better category coverage.

## Tests

```
pytest tests/
```

`tests/fixtures/sample_raw.csv` is a handcrafted 7-row sample covering a
duplicate row, a cancellation, a negative-quantity row, a zero-price row,
and a missing customer id, used to verify `clean()` and `transform()`
behavior without needing the full 540k-row dataset.
