# Databricks Pipelines

This directory contains repo-scaffolded Databricks Lakeflow Declarative Pipeline assets.

The first pipeline is written in PySpark and includes bronze, silver, and the first gold mart:

- `northmart_bronze.py`
- `northmart_silver_gold.py`

It is deployed and run via the root `databricks.yml` Asset Bundle (serverless, `dev` target). See [docs/databricks-deploy-run.md](../../docs/databricks-deploy-run.md) for the deploy/run runbook and [docs/databricks-incremental-replay.md](../../docs/databricks-incremental-replay.md) for the incremental replay demonstration.

## Expected Raw Volume Layout

Generated local files from `src/northmart_data_prep` should eventually be uploaded to a Unity Catalog volume using this folder shape:

```text
/Volumes/<catalog>/<schema>/<volume>/northmart_thin_slice/
  raw_freshretailnet_daily/
    raw_freshretailnet_daily.csv
  northmart_store_master/
    northmart_store_master.csv
  northmart_product_master/
    northmart_product_master.csv
```

The PySpark pipeline expects the parent path through this Spark pipeline configuration key:

```text
raw_data_path=/Volumes/<catalog>/<schema>/<volume>/northmart_thin_slice
```

## Bronze Tables

The pipeline creates:

- `bronze_raw_freshretailnet_daily`
- `bronze_northmart_store_master`
- `bronze_northmart_product_master`

Each table uses Auto Loader in CSV mode and adds:

- `_source_file`
- `_loaded_at`

The source-provided `ingested_at` value is preserved and cast to timestamp.

Bronze is an append-only landing log: the raw daily table carries a `batch_seq`
(monotonic load sequence). Because Auto Loader only ingests newly landed files,
re-running the pipeline after landing a new batch ingests just that batch. A
corrected or late-arriving observation lands as an additional row for the same
grain, preserving full audit history.

## Silver Tables

The pipeline also creates:

- `dim_store`
- `dim_product`
- `dim_date`
- `fact_sales`
- `fact_inventory_status`
- `fact_promotion`
- `fact_external_signal`

Silver tables map encoded public source identifiers to NorthMart business keys, derive planner-friendly measures, and apply simple quality expectations aligned with `data_contracts/`.

Silver also reconciles restatements: a shared `latest_raw()` helper keeps only
the newest version per `(store, product, date)` grain (ordered by `batch_seq`),
so corrected and late-arriving records flow through every fact without
duplicating the grain. Bronze stays incremental; silver/gold recompute
cumulatively from bronze each run.

The `dim_` and `fact_` prefixes are intentional even though these tables live in the silver layer. In this project, silver is the trusted, conformed, analyst-queryable schema. The prefixes describe modeling role:

- `dim_*`: conformed descriptive entities.
- `fact_*`: conformed measurable events or daily observations.

Gold remains the curated decision layer.

## Gold Mart

The first gold mart is:

- `gold_store_product_stockout_daily`

This mart joins conformed dimensions and facts to answer the first planner questions: stockout exposure, estimated revenue impact, promotion-supported demand, and priority tier.

## Implementation Notes

- Uses `from pyspark import pipelines as dp`.
- Does not use legacy `import dlt`.
- Uses `spark.readStream.format("cloudFiles")`.
- Uses PySpark transformations for silver conformance and gold serving logic.
- Keeps all real catalog, schema, and volume names out of source control.
- Defers actual Databricks deployment until a later checkpoint.
