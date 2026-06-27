# Databricks Bronze Ingestion

## Purpose

This checkpoint introduces the first Databricks Lakeflow Declarative Pipeline scaffold for NorthMart. It focuses only on bronze ingestion.

The pipeline is written in PySpark and is designed to read the generated NorthMart thin-slice CSV files after they are uploaded to a Unity Catalog volume.

## Current Status

This is a repo scaffold only.

Not done yet:

- No files have been uploaded to Unity Catalog.
- No Databricks pipeline has been deployed.
- No Databricks CLI commands have been run for this checkpoint.

## Local To Future Databricks Mapping

Local generator output:

```text
data/generated/northmart_thin_slice/
  raw_freshretailnet_daily.csv
  northmart_store_master.csv
  northmart_product_master.csv
```

Future Unity Catalog volume layout:

```text
/Volumes/<catalog>/<schema>/<volume>/northmart_thin_slice/
  raw_freshretailnet_daily/
    raw_freshretailnet_daily.csv
  northmart_store_master/
    northmart_store_master.csv
  northmart_product_master/
    northmart_product_master.csv
```

Pipeline configuration:

```text
raw_data_path=/Volumes/<catalog>/<schema>/<volume>/northmart_thin_slice
```

## Bronze Tables

| Bronze table | Source folder | Purpose |
| --- | --- | --- |
| `bronze_raw_freshretailnet_daily` | `raw_freshretailnet_daily/` | Source-shaped demand, stockout, promotion, holiday, and weather signals. |
| `bronze_northmart_store_master` | `northmart_store_master/` | Synthetic NorthMart store master. |
| `bronze_northmart_product_master` | `northmart_product_master/` | Synthetic NorthMart product master. |

## Why PySpark LDP

The project uses PySpark Lakeflow Declarative Pipelines for this layer because:

- The user explicitly chose PySpark for Lakeflow Declarative Pipelines.
- The source files include array-like fields that are easier to parse in PySpark.
- The project will later need conformance logic that benefits from reusable Python helpers.

## Next Decision

After this scaffold, choose one of two paths:

- Upload generated files to a Unity Catalog volume and deploy the bronze pipeline.
- Add silver conformance logic in PySpark before deploying.
