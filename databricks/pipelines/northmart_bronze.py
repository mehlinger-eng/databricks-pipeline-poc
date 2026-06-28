from __future__ import annotations

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)


# Per-layer fully-qualified prefixes. The pipeline targets a single catalog
# (set via the `catalog` configuration key) and spans the bronze/silver/gold
# schemas using fully-qualified dataset names.
CATALOG = spark.conf.get("catalog")
BRONZE = f"{CATALOG}.bronze"
SILVER = f"{CATALOG}.silver"
GOLD = f"{CATALOG}.gold"


RAW_FRESHRETAILNET_SCHEMA = StructType(
    [
        StructField("city_id", LongType(), True),
        StructField("store_id", LongType(), True),
        StructField("management_group_id", LongType(), True),
        StructField("first_category_id", LongType(), True),
        StructField("second_category_id", LongType(), True),
        StructField("third_category_id", LongType(), True),
        StructField("product_id", LongType(), True),
        StructField("dt", StringType(), True),
        StructField("sale_amount", DoubleType(), True),
        StructField("hours_sale", StringType(), True),
        StructField("stock_hour6_22_cnt", LongType(), True),
        StructField("hours_stock_status", StringType(), True),
        StructField("discount", DoubleType(), True),
        StructField("holiday_flag", LongType(), True),
        StructField("activity_flag", LongType(), True),
        StructField("precpt", DoubleType(), True),
        StructField("avg_temperature", DoubleType(), True),
        StructField("avg_humidity", DoubleType(), True),
        StructField("avg_wind_level", DoubleType(), True),
        StructField("source_dataset", StringType(), True),
        StructField("source_split", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("ingested_at", StringType(), True),
    ]
)

STORE_MASTER_SCHEMA = StructType(
    [
        StructField("northmart_store_id", StringType(), True),
        StructField("source_store_id", LongType(), True),
        StructField("store_name", StringType(), True),
        StructField("region", StringType(), True),
        StructField("state", StringType(), True),
        StructField("city", StringType(), True),
        StructField("store_format", StringType(), True),
        StructField("climate_zone", StringType(), True),
        StructField("opened_date", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("ingested_at", StringType(), True),
    ]
)

PRODUCT_MASTER_SCHEMA = StructType(
    [
        StructField("northmart_product_id", StringType(), True),
        StructField("source_product_id", LongType(), True),
        StructField("product_name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("subcategory", StringType(), True),
        StructField("brand", StringType(), True),
        StructField("replenishment_class", StringType(), True),
        StructField("base_unit_price", DoubleType(), True),
        StructField("seasonal_peak", StringType(), True),
        StructField("batch_id", StringType(), True),
        StructField("ingested_at", StringType(), True),
    ]
)


def raw_data_path(dataset_name: str) -> str:
    base_path = spark.conf.get("raw_data_path")
    return f"{base_path.rstrip('/')}/{dataset_name}"


def read_csv_stream(dataset_name: str, schema: StructType):
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "false")
        .option("header", "true")
        .schema(schema)
        .load(raw_data_path(dataset_name))
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_loaded_at", F.current_timestamp())
    )


@dp.table(
    name=f"{BRONZE}.bronze_raw_freshretailnet_daily",
    comment="Raw FreshRetailNet-like daily demand and stockout observations for the NorthMart thin slice.",
    cluster_by=["dt", "store_id"],
)
@dp.expect_or_drop("valid_raw_business_key", "city_id IS NOT NULL AND store_id IS NOT NULL AND product_id IS NOT NULL AND dt IS NOT NULL")
@dp.expect_or_drop("valid_sales_amount", "sale_amount >= 0")
@dp.expect_or_drop("valid_stockout_hours", "stock_hour6_22_cnt >= 0 AND stock_hour6_22_cnt <= 17")
@dp.expect_or_drop("valid_discount", "discount > 0 AND discount <= 1")
def bronze_raw_freshretailnet_daily():
    raw = read_csv_stream("raw_freshretailnet_daily", RAW_FRESHRETAILNET_SCHEMA)
    return (
        raw.withColumn("dt", F.to_date("dt"))
        .withColumn("hours_sale", F.from_json("hours_sale", ArrayType(DoubleType())))
        .withColumn("hours_stock_status", F.from_json("hours_stock_status", ArrayType(LongType())))
        .withColumn("ingested_at", F.to_timestamp("ingested_at"))
    )


@dp.table(
    name=f"{BRONZE}.bronze_northmart_store_master",
    comment="Raw synthetic NorthMart store master records for the thin slice.",
    cluster_by=["region", "state"],
)
@dp.expect_or_drop("valid_store_key", "northmart_store_id IS NOT NULL")
@dp.expect_or_drop("valid_store_format", "store_format IN ('flagship', 'standard', 'outlet')")
def bronze_northmart_store_master():
    return (
        read_csv_stream("northmart_store_master", STORE_MASTER_SCHEMA)
        .withColumn("opened_date", F.to_date("opened_date"))
        .withColumn("ingested_at", F.to_timestamp("ingested_at"))
    )


@dp.table(
    name=f"{BRONZE}.bronze_northmart_product_master",
    comment="Raw synthetic NorthMart product master records for the thin slice.",
    cluster_by=["category", "replenishment_class"],
)
@dp.expect_or_drop("valid_product_key", "northmart_product_id IS NOT NULL")
@dp.expect_or_drop("valid_unit_price", "base_unit_price > 0")
@dp.expect_or_drop("valid_replenishment_class", "replenishment_class IN ('fast', 'standard', 'slow', 'seasonal')")
def bronze_northmart_product_master():
    return read_csv_stream("northmart_product_master", PRODUCT_MASTER_SCHEMA).withColumn(
        "ingested_at", F.to_timestamp("ingested_at")
    )
