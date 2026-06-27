# Data Contracts

Contracts describe the expected shape, grain, keys, and quality checks for the first NorthMart thin slice.

The contracts are intentionally implementation-neutral. They can guide local data generation, Databricks ingestion, SQL transformations, and validation checks.

## Layers

- `bronze/`: raw source-shaped inputs and synthetic NorthMart master data.
- `silver/`: conformed entities with stable business keys.
- `gold/`: business-ready serving tables.

## Thin Slice Contract Set

Bronze:

- `bronze/raw_freshretailnet_daily.yml`
- `bronze/northmart_store_master.yml`
- `bronze/northmart_product_master.yml`

Silver:

- `silver/dim_store.yml`
- `silver/dim_product.yml`
- `silver/dim_date.yml`
- `silver/fact_sales.yml`
- `silver/fact_inventory_status.yml`
- `silver/fact_promotion.yml`
- `silver/fact_external_signal.yml`

Gold:

- `gold/gold_store_product_stockout_daily.yml`
