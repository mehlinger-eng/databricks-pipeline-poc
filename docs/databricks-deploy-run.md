# Deploy and Run: First NorthMart Pipeline

This document captures the first end-to-end deployment and run of the NorthMart
medallion Lakeflow Declarative Pipeline on Databricks Free Edition, including the
exact commands, the Unity Catalog target layout, and the observed results.

## Target Layout

- **Catalog:** `northmart` (created with Default Storage)
- **Schemas:** `bronze`, `silver`, `gold`
- **Landing volume:** `northmart.bronze.landing`
- **Raw base path:** `/Volumes/northmart/bronze/landing/northmart_thin_slice/<dataset>/`
- **Pipeline:** `northmart-medallion-pipeline` (serverless, single pipeline spanning all three schemas via fully-qualified table names)

The pipeline source reads two Spark configuration keys, supplied by the bundle:

- `catalog` — drives the `BRONZE`/`SILVER`/`GOLD` fully-qualified prefixes.
- `raw_data_path` — base path under the landing volume; the bronze Auto Loader
  appends each dataset name as a subfolder.

## Prerequisites Verified

- Databricks CLI `v1.2.1`, `DEFAULT` profile valid against
  `https://dbc-cc82131f-4015.cloud.databricks.com`.
- A serverless SQL warehouse (`Serverless Starter Warehouse`) is available for
  UC provisioning and verification queries.
- Catalog creation: the CLI `catalogs create` path fails on Free Edition
  (Default Storage requires a managed location), but `CREATE CATALOG` via the
  SQL warehouse auto-uses Default Storage and succeeds.

## Step-by-Step Commands

### 1. Provision Unity Catalog (SQL warehouse)

Run via the Statement Execution API against the serverless warehouse:

```sql
CREATE CATALOG IF NOT EXISTS northmart COMMENT 'NorthMart retail lakehouse POC';
CREATE SCHEMA  IF NOT EXISTS northmart.bronze;
CREATE SCHEMA  IF NOT EXISTS northmart.silver;
CREATE SCHEMA  IF NOT EXISTS northmart.gold;
CREATE VOLUME  IF NOT EXISTS northmart.bronze.landing;
```

### 2. Generate + validate the thin slice locally

```bash
PYTHONPATH=src python3 -m northmart_data_prep.generate --source synthetic
PYTHONPATH=src python3 -m northmart_data_prep.validate
```

### 3. Upload CSVs to the landing volume (one subfolder per dataset)

```bash
BASE="dbfs:/Volumes/northmart/bronze/landing/northmart_thin_slice"
SRC="data/generated/northmart_thin_slice"
for ds in raw_freshretailnet_daily northmart_store_master northmart_product_master; do
  databricks fs mkdir "$BASE/$ds" --profile DEFAULT
  databricks fs cp "$SRC/$ds.csv" "$BASE/$ds/$ds.csv" --overwrite --profile DEFAULT
done
```

### 4. Validate, deploy, and run the bundle

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy   -t dev --profile DEFAULT
databricks bundle run northmart_bronze_pipeline -t dev --profile DEFAULT
```

## Observed Results

The pipeline ran all 10 flows to `COMPLETED` (bronze → silver → gold) on
serverless in roughly 1.5 minutes of compute after resource warm-up.

### Row counts

| Table | Rows |
| --- | --- |
| `bronze.bronze_raw_freshretailnet_daily` | 57,600 |
| `bronze.bronze_northmart_store_master` | 8 |
| `bronze.bronze_northmart_product_master` | 80 |
| `silver.dim_store` | 8 |
| `silver.dim_product` | 80 |
| `silver.dim_date` | 90 |
| `silver.fact_sales` | 57,600 |
| `silver.fact_inventory_status` | 57,600 |
| `silver.fact_promotion` | 57,600 |
| `silver.fact_external_signal` | 720 |
| `gold.gold_store_product_stockout_daily` | 57,600 |

Counts match expectations: `57,600 = 8 stores × 80 products × 90 days`, and the
store-date grained `fact_external_signal` is `8 × 90 = 720`. No expectation drops
reduced row counts, and the gold mart preserves full grain (every sales row
joined to its dimensions).

### Gold mart sanity checks

- Negative `estimated_revenue`: 0; negative `lost_sales_proxy`: 0; null `priority_tier`: 0.
- Stockout rows (`stockout_flag = true`): 9,083.
- `priority_tier` distribution: `low` 46,130 · `critical` 8,871 · `high` 2,418 · `medium` 181.
- Top critical rows surface the highest lost-sales-proxy store/product/day
  combinations (e.g. Hydration and Camping SKUs in the Rockies region with 7-8
  stockout hours), which is the intended planner-facing signal.

## Notes and Gotchas

- **Catalog creation on Free Edition:** prefer `CREATE CATALOG` via SQL (auto
  Default Storage) over the CLI `catalogs create`, which demands a managed
  location.
- **Landing subfolders:** `databricks fs cp` does not create intermediate volume
  directories — `databricks fs mkdir` each dataset subfolder first.
- **Single pipeline, multi-schema:** all datasets live in one serverless pipeline
  and publish across `bronze`/`silver`/`gold` via fully-qualified `@dp.table`
  names, honoring the Free Edition one-active-pipeline guidance.

## Re-running

Re-running `databricks bundle run northmart_bronze_pipeline -t dev --profile DEFAULT`
is incremental for the streaming bronze tables (Auto Loader tracks processed
files) and recomputes the gold materialized view. To ingest a new batch, drop
additional CSVs into the dataset subfolders and re-run.
