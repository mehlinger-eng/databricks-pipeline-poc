# Databricks Medallion Pipeline

## Purpose

This document describes the repo-scaffolded PySpark Lakeflow Declarative Pipeline for the NorthMart thin slice.

The pipeline is still source-control only. It has not been deployed to Databricks and has not written to Unity Catalog.

## Pipeline Files

- `databricks/pipelines/northmart_bronze.py`: bronze ingestion from future Unity Catalog volume paths.
- `databricks/pipelines/northmart_silver_gold.py`: silver conformance and the first gold stockout mart.

## Layer Naming Convention

NorthMart uses medallion schemas plus modeling-role table names:

```text
<catalog>.bronze.bronze_raw_freshretailnet_daily
<catalog>.silver.dim_store
<catalog>.silver.dim_product
<catalog>.silver.fact_sales
<catalog>.gold.gold_store_product_stockout_daily
```

The `dim_` and `fact_` prefixes are intentional in silver. They describe the table's analytical role, not its serving tier.

- Bronze tables are source-shaped and ingestion-oriented.
- Silver tables are trusted, conformed, quality-checked, and analyst-queryable.
- Gold tables are curated, decision-ready marts for dashboards, stakeholder workflows, and model-serving outputs.

Analysts can query silver directly for exploration and QA. Business dashboards should default to gold unless they need flexible analysis over conformed building blocks.

## Medallion Flow

```text
Generated CSV files
  -> bronze_raw_freshretailnet_daily
  -> bronze_northmart_store_master
  -> bronze_northmart_product_master
  -> dim_store
  -> dim_product
  -> dim_date
  -> fact_sales
  -> fact_inventory_status
  -> fact_promotion
  -> fact_external_signal
  -> gold_store_product_stockout_daily
```

## Silver Conformance

Silver logic maps public-source identifiers into NorthMart business keys:

- `store_id` -> `store_key`
- `product_id` -> `product_key`
- `dt` -> `date_key`

It also derives:

- `observed_units`
- `estimated_revenue`
- `stockout_hours`
- `stockout_flag`
- `discount_rate`
- `promotion_flag`
- `demand_signal_bucket`

## Gold Mart

`gold_store_product_stockout_daily` is the first business-serving table.

It has one row per store, product, and date. It combines:

- Store attributes.
- Product attributes.
- Observed demand and estimated revenue.
- Stockout status.
- Promotion and discount context.
- Holiday and demand-signal context.
- Lost-sales proxy.
- Rules-based stockout risk score.
- Planner priority tier.

## Deployment Status

Deployment is intentionally deferred.

Before running in Databricks, we still need to:

- Upload generated CSVs to the expected Unity Catalog volume layout.
- Choose catalog, schema, and volume names.
- Wire the reference pipeline resource into a root `databricks.yml`.
- Validate the pipeline in Databricks Free Edition.
