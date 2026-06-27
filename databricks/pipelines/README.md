# Databricks Pipelines

This directory contains repo-scaffolded Databricks Lakeflow Declarative Pipeline assets.

The first pipeline is intentionally bronze-only and written in PySpark:

- `northmart_bronze.py`

It is not deployed yet. The next checkpoint will decide whether to upload generated files to a Unity Catalog volume and run this pipeline, or continue building silver conformance first.

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

## Implementation Notes

- Uses `from pyspark import pipelines as dp`.
- Does not use legacy `import dlt`.
- Uses `spark.readStream.format("cloudFiles")`.
- Keeps all real catalog, schema, and volume names out of source control.
- Defers actual Databricks deployment until a later checkpoint.
