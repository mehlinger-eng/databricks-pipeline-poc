# Databricks Pipelines

This directory contains repo-scaffolded Databricks Lakeflow Declarative Pipeline assets.

The first pipeline is written in PySpark and currently includes bronze, silver, and the first gold mart:

- `northmart_bronze.py`
- `northmart_silver_gold.py`

It is not deployed yet. The next checkpoint will decide whether to upload generated files to a Unity Catalog volume and run the pipeline.

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
