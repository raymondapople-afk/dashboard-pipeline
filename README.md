# Dashboard Data Pipeline

A reusable pipeline that turns messy, differently-shaped client CSV exports
into a standard analytics schema, then produces two outputs from that single
clean dataset:

1. A flat cleaned CSV (`data/processed/<client>_clean.csv`) to point a BI
   tool (e.g. Looker Studio) at.
2. Pre-aggregated JSON files (`data/exports/*.json`), inlined directly into a
   self-contained HTML dashboard (`dashboard/<client>_dashboard.html`) that
   opens in any browser with no server or build step.

The goal is reusability: the core cleaning/transform code never references
a specific client's column names, file structure, or quirks — onboarding a
new client is a matter of writing a config file, not touching pipeline code.
This has been validated across three structurally different real-world
datasets (UK e-commerce line items, coffee shop POS transactions, and hotel
bookings) — see [Adding a new client](#adding-a-new-client) below for what
each one needed.

## Try it

Open any of the prebuilt dashboards directly — no setup required:
- [`dashboard/uk_ecommerce_dashboard.html`](dashboard/uk_ecommerce_dashboard.html)
- [`dashboard/coffee_shop_dashboard.html`](dashboard/coffee_shop_dashboard.html)
- [`dashboard/hotel_bookings_dashboard.html`](dashboard/hotel_bookings_dashboard.html)

Each is a static file with its dataset's aggregates baked in — just open it
in a browser.

## Project layout

```
pipeline/        cleaning/transform/export code, generic across clients
config/clients/  one YAML per client describing its raw schema and quirks
data/raw/        raw client CSV exports (input)
data/processed/  cleaned, standard-schema CSV (output, for BI tools)
data/exports/    pre-aggregated JSON used to build the dashboards (output)
dashboard/       standalone HTML dashboards, one per client
tests/           pytest suite + handcrafted CSV fixtures
```

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

The cleaning/transform code (`pipeline/clean.py`, `pipeline/transform.py`,
`pipeline/ingest.py`) never references a specific client's column names — it
only knows the standard schema above. To onboard a new client:

1. Drop their raw CSV in `data/raw/`.
2. Copy `config/clients/uk_ecommerce.yaml` to `config/clients/<new_client>.yaml`
   and edit:
   - `column_map` — map their raw column headers to the standard field names.
   - `date_format` — the `strptime` format of their date column.
   - `encoding` — defaults to `"utf-8-sig"` (handles plain UTF-8 and UTF-8
     with a BOM). Override only if the export uses something else, e.g.
     `"latin1"` for files with raw non-UTF-8 bytes (check with
     `file <path>` / try decoding — don't guess).
   - `date_columns` — only needed if date and time-of-day are two separate
     raw columns instead of one combined timestamp (e.g. POS exports). When
     set, they're joined space-separated into a single `date` field before
     parsing with `date_format`.
   - `constants` — for standard fields with no raw column equivalent at all
     (e.g. anonymous transactions with no `customer_id`, single-country
     exports with no `country` column). Maps the standard field name to a
     literal value used for every row.
   - `cancellation_prefix` — the order-id prefix that marks a cancelled order
     (set to something that will never match, e.g. `"__NONE__"`, if N/A).
   - `category_rules` — keyword → category buckets for their product catalog,
     only needed if the client has **no** real category column. Rules use
     word-boundary matching (`re.search(r"\bword\b", ...)`), not "first
     match wins" alphabetically — order rules from most to least specific.
     Unmatched products fall back to `"Uncategorized"`. If the client *does*
     have a real category column, map it directly via `column_map` instead
     (e.g. `product_category: category`) and leave `category_rules` empty —
     `transform.py` passes through an already-populated `category` column
     rather than overwriting it with keyword derivation.
   - `sum_columns` — for a standard field that's the sum of two or more raw
     columns rather than one (e.g. nights stayed = weekend nights + week
     nights). Maps the standard field name to a list of raw source columns.
   - `synthesize_order_id` — set to `true` if the export has no primary key
     column at all. `order_id` is generated from row position so order-count
     aggregations (`nunique(order_id)`) still work correctly.
   - `exclude_rows` — generalized row filtering by column value (e.g.
     `[{column: is_canceled, equals: "1"}]`), for clients whose
     cancellation/void signal is a column value rather than an `order_id`
     prefix like `cancellation_prefix` expects.
   - `drop_duplicates` — defaults to `true`. Set to `false` if the export has
     no primary key and exact-duplicate rows can't be told apart from two
     genuinely distinct records that happen to share every attribute —
     blanket-dropping in that case risks silently discarding real revenue.
3. Run:
   ```
   python -m pipeline.run --client <new_client> --input data/raw/<their_file>.csv
   ```

No changes to `pipeline/*.py` should be needed for a differently-shaped
client CSV — confirmed by onboarding a second and third, structurally
different dataset:
- `config/clients/coffee_shop.yaml`: split date/time columns, no customer or
  country columns at all, a real category column (needed `encoding`,
  `date_columns`, `constants`, and the category-passthrough fix).
- `config/clients/hotel_bookings.yaml`: booking data with no primary key
  column at all, a quantity that's the sum of two raw columns, and a
  cancellation signal that's a column value rather than an `order_id`
  prefix (needed `sum_columns`, `synthesize_order_id`, `exclude_rows`, and
  `drop_duplicates`). Notably, `transform.py` itself needed **zero** changes
  for this client — its revenue formula (`quantity * unit_price`) already
  was `adr × nights`; every gap was in how `ingest.py`/`clean.py` produce
  and filter rows upstream of it.

## Notes on the coffee shop dataset

- Anonymous point-of-sale data: every row is `customer_id: "GUEST"` and
  `country: "USA"` (via `constants` in the config) since the export has no
  customer identity or country column at all. `customer_trends.json` is
  consequently degenerate for this client — a single row covering every
  transaction — it's a real reflection of the data, not a pipeline bug.
- `category` comes straight from the real `product_category` column, not
  keyword derivation — no `Uncategorized` noise.
- Data is very clean: 0 duplicate rows, 0 non-positive quantity/price, 0
  blank fields, so `excluded_descriptions` and `cancellation_prefix` are
  unused for this client (`cancellation_prefix` is set to a value that can
  never match, since the export has no cancellation concept).
- `hour` correctly reflects time of day (combined from separate
  `transaction_date` / `transaction_time` columns via `date_columns`) and
  shows a realistic coffee-shop morning rush (peak 06:00–10:00), unlike the
  UK retailer's midday peak.

## Notes on the hotel bookings dataset

- Booking/appointment data, not per-item sales: `revenue = adr × nights
  stayed`, where `nights` is `sum_columns`-derived from
  `stays_in_weekend_nights + stays_in_week_nights`.
- No primary key column exists in this export at all — `order_id` is
  synthesized from row position (`synthesize_order_id`). No customer
  identity column either — `customer_id` is `"GUEST"` via `constants`, same
  as the coffee shop client. `customer_trends.json` is degenerate here too.
- Cancellations/no-shows (`is_canceled == "1"`, ~37% of rows) are excluded
  entirely via `exclude_rows`, consistent with how the other two clients
  handle returns/cancellations — but expressed as a column-value match
  rather than an `order_id` prefix, since this export has no such prefix.
- `drop_duplicates: false` — 27% of rows are exact duplicates across every
  column, but with no primary key there's no way to confirm whether that's
  a real data-entry error or two distinct bookings that happen to share
  every attribute. Blanket-dropping them (like the other two clients do)
  would risk silently discarding real revenue, so this client keeps them.
- `hour` is `0` for every row — this export captures only an arrival
  *date*, no time-of-day at all. Unlike the coffee shop's split
  date/time columns, this isn't fixable by combining columns; the data
  simply doesn't capture it. A real data limitation, not a pipeline bug.
- ~488 rows (0.4%) have the literal string `"NULL"` as `country` rather
  than blank. Left as-is — not worth a structural fix for 0.4% of rows.

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
