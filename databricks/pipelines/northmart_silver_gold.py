from __future__ import annotations

from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.window import Window


SERVICE_WINDOW_HOURS = 17

# Per-layer fully-qualified prefixes. The pipeline targets a single catalog
# (set via the `catalog` configuration key) and spans the bronze/silver/gold
# schemas using fully-qualified dataset names.
CATALOG = spark.conf.get("catalog")
BRONZE = f"{CATALOG}.bronze"
SILVER = f"{CATALOG}.silver"
GOLD = f"{CATALOG}.gold"


def latest_raw():
    """Reduce the append-only bronze landing log to the latest version per grain.

    Bronze is an immutable record of everything that landed, so a corrected or
    late-arriving observation appears as an additional row for the same
    (store, product, date) grain. Silver keeps only the newest version, ordered
    by ``batch_seq`` (then ``_loaded_at`` as a tiebreak), so restatements flow
    through to every downstream fact without duplicating the grain.
    """
    dedup_window = Window.partitionBy(
        "store_id", "product_id", "dt"
    ).orderBy(F.col("batch_seq").desc_nulls_last(), F.col("_loaded_at").desc_nulls_last())
    return (
        spark.read.table(f"{BRONZE}.bronze_raw_freshretailnet_daily")
        .withColumn("_version_rank", F.row_number().over(dedup_window))
        .filter(F.col("_version_rank") == 1)
        .drop("_version_rank")
    )


def raw_with_keys():
    return (
        latest_raw().alias("raw")
        .join(
            spark.read.table(f"{BRONZE}.bronze_northmart_store_master").alias("store"),
            F.col("raw.store_id") == F.col("store.source_store_id"),
            "inner",
        )
        .join(
            spark.read.table(f"{BRONZE}.bronze_northmart_product_master").alias("product"),
            F.col("raw.product_id") == F.col("product.source_product_id"),
            "inner",
        )
    )


@dp.table(
    name=f"{SILVER}.dim_store",
    comment="Conformed NorthMart store dimension for the thin slice.",
    cluster_by=["region", "state"],
)
@dp.expect_or_drop("valid_store_key", "store_key IS NOT NULL")
def dim_store():
    return (
        spark.read.table(f"{BRONZE}.bronze_northmart_store_master")
        .select(
            F.col("northmart_store_id").alias("store_key"),
            "source_store_id",
            "store_name",
            "region",
            "state",
            "city",
            "store_format",
            "climate_zone",
            F.coalesce(F.col("opened_date"), F.to_date(F.lit("1900-01-01"))).alias("effective_start_date"),
            F.lit(None).cast("date").alias("effective_end_date"),
            F.lit(True).alias("is_current"),
        )
        .dropDuplicates(["store_key"])
    )


@dp.table(
    name=f"{SILVER}.dim_product",
    comment="Conformed NorthMart product dimension for the thin slice.",
    cluster_by=["category", "replenishment_class"],
)
@dp.expect_or_drop("valid_product_key", "product_key IS NOT NULL")
@dp.expect_or_drop("valid_base_unit_price", "base_unit_price > 0")
def dim_product():
    return (
        spark.read.table(f"{BRONZE}.bronze_northmart_product_master")
        .select(
            F.col("northmart_product_id").alias("product_key"),
            "source_product_id",
            "product_name",
            "category",
            "subcategory",
            "brand",
            "replenishment_class",
            "base_unit_price",
            "seasonal_peak",
            F.lit(True).alias("is_active"),
        )
        .dropDuplicates(["product_key"])
    )


@dp.table(
    name=f"{SILVER}.dim_date",
    comment="Conformed date dimension for the NorthMart thin slice.",
    cluster_by=["year", "month"],
)
@dp.expect_or_drop("valid_date_key", "date_key IS NOT NULL")
def dim_date():
    return (
        latest_raw()
        .select(F.col("dt").alias("date_key"), F.col("holiday_flag"))
        .dropDuplicates(["date_key"])
        .withColumn("day_of_week", F.date_format("date_key", "EEEE"))
        .withColumn("week_start_date", F.date_trunc("week", F.col("date_key")).cast("date"))
        .withColumn("month", F.month("date_key"))
        .withColumn("quarter", F.quarter("date_key"))
        .withColumn("year", F.year("date_key"))
        .withColumn("is_weekend", F.dayofweek("date_key").isin(1, 7))
        .withColumn("is_holiday", F.col("holiday_flag") == 1)
        .withColumn(
            "planning_season",
            F.when(F.col("month").isin(3, 4, 5), "spring")
            .when(F.col("month").isin(6, 7, 8), "summer")
            .when(F.col("month").isin(9, 10, 11), "fall")
            .otherwise("winter"),
        )
        .drop("holiday_flag")
    )


@dp.table(
    name=f"{SILVER}.fact_sales",
    comment="Conformed daily observed demand and estimated revenue fact.",
    cluster_by=["date_key", "store_key"],
)
@dp.expect_or_drop("valid_sales_keys", "store_key IS NOT NULL AND product_key IS NOT NULL AND date_key IS NOT NULL")
@dp.expect_or_drop("valid_observed_units", "observed_units >= 0")
@dp.expect_or_drop("valid_estimated_revenue", "estimated_revenue >= 0")
def fact_sales():
    keyed = raw_with_keys()
    observed_units = F.round(F.col("raw.sale_amount") * F.lit(10.0), 2)
    discount_rate = F.round(F.lit(1.0) - F.col("raw.discount"), 4)

    return keyed.select(
        F.col("store.northmart_store_id").alias("store_key"),
        F.col("product.northmart_product_id").alias("product_key"),
        F.col("raw.dt").alias("date_key"),
        observed_units.alias("observed_units"),
        F.col("raw.sale_amount").alias("normalized_sales_amount"),
        F.round(observed_units * F.col("product.base_unit_price") * (F.lit(1.0) - discount_rate), 2).alias(
            "estimated_revenue"
        ),
        F.col("raw.source_dataset"),
        F.col("raw.batch_id"),
        F.current_timestamp().alias("processed_at"),
    )


@dp.table(
    name=f"{SILVER}.fact_inventory_status",
    comment="Conformed daily stockout status fact.",
    cluster_by=["date_key", "store_key"],
)
@dp.expect_or_drop("valid_inventory_keys", "store_key IS NOT NULL AND product_key IS NOT NULL AND date_key IS NOT NULL")
@dp.expect_or_drop("valid_stockout_hours", "stockout_hours >= 0 AND stockout_hours <= service_window_hours")
def fact_inventory_status():
    keyed = raw_with_keys()
    stockout_hours = F.col("raw.stock_hour6_22_cnt").cast("int")

    return keyed.select(
        F.col("store.northmart_store_id").alias("store_key"),
        F.col("product.northmart_product_id").alias("product_key"),
        F.col("raw.dt").alias("date_key"),
        stockout_hours.alias("stockout_hours"),
        (stockout_hours > 0).alias("stockout_flag"),
        F.lit(SERVICE_WINDOW_HOURS).alias("service_window_hours"),
        F.when(stockout_hours == 0, "healthy")
        .when(stockout_hours <= 2, "watch")
        .when(stockout_hours <= 6, "at_risk")
        .otherwise("stockout")
        .alias("inventory_coverage_status"),
        F.col("raw.batch_id"),
        F.current_timestamp().alias("processed_at"),
    )


@dp.table(
    name=f"{SILVER}.fact_promotion",
    comment="Conformed daily promotion and discount fact.",
    cluster_by=["date_key", "store_key"],
)
@dp.expect_or_drop("valid_promotion_keys", "store_key IS NOT NULL AND product_key IS NOT NULL AND date_key IS NOT NULL")
@dp.expect_or_drop("valid_discount_rate", "discount_rate >= 0 AND discount_rate < 1")
def fact_promotion():
    keyed = raw_with_keys()
    discount_rate = F.round(F.lit(1.0) - F.col("raw.discount"), 4)

    return keyed.select(
        F.col("store.northmart_store_id").alias("store_key"),
        F.col("product.northmart_product_id").alias("product_key"),
        F.col("raw.dt").alias("date_key"),
        ((F.col("raw.activity_flag") == 1) | (discount_rate > 0)).alias("promotion_flag"),
        discount_rate.alias("discount_rate"),
        F.when(F.col("raw.activity_flag") == 1, F.lit("Seasonal Demand Push"))
        .when(discount_rate > 0, F.lit("Markdown Support"))
        .otherwise(F.lit(None))
        .alias("campaign_name"),
        F.col("raw.batch_id"),
        F.current_timestamp().alias("processed_at"),
    )


@dp.table(
    name=f"{SILVER}.fact_external_signal",
    comment="Conformed daily weather, holiday, and event context.",
    cluster_by=["date_key", "store_key"],
)
@dp.expect_or_drop("valid_external_keys", "store_key IS NOT NULL AND date_key IS NOT NULL")
@dp.expect_or_drop(
    "valid_demand_signal_bucket",
    "demand_signal_bucket IN ('normal', 'weather_sensitive', 'holiday', 'event', 'compound')",
)
def fact_external_signal():
    keyed = raw_with_keys()
    aggregated = (
        keyed.groupBy(
            F.col("store.northmart_store_id").alias("store_key"),
            F.col("raw.dt").alias("date_key"),
        )
        .agg(
            F.max(F.col("raw.holiday_flag")).alias("holiday_flag"),
            F.max(F.col("raw.activity_flag")).alias("activity_flag"),
            F.avg("raw.precpt").alias("precipitation"),
            F.avg("raw.avg_temperature").alias("avg_temperature"),
            F.avg("raw.avg_humidity").alias("avg_humidity"),
            F.avg("raw.avg_wind_level").alias("avg_wind_level"),
            F.max("raw.batch_id").alias("batch_id"),
        )
    )
    local_event_flag = F.col("activity_flag") == 1
    is_holiday = F.col("holiday_flag") == 1
    weather_sensitive = (F.col("precipitation") > 0.2) | (F.col("avg_wind_level") > 6)

    return aggregated.select(
        "store_key",
        "date_key",
        is_holiday.alias("is_holiday"),
        local_event_flag.alias("local_event_flag"),
        F.round("precipitation", 4).alias("precipitation"),
        F.round("avg_temperature", 2).alias("avg_temperature"),
        F.round("avg_humidity", 2).alias("avg_humidity"),
        F.round("avg_wind_level", 2).alias("avg_wind_level"),
        F.when(is_holiday & local_event_flag, "compound")
        .when(is_holiday, "holiday")
        .when(local_event_flag, "event")
        .when(weather_sensitive, "weather_sensitive")
        .otherwise("normal")
        .alias("demand_signal_bucket"),
        "batch_id",
        F.current_timestamp().alias("processed_at"),
    )


@dp.materialized_view(
    name=f"{GOLD}.gold_store_product_stockout_daily",
    comment="Daily store-product stockout analysis mart for NorthMart planners.",
    cluster_by=["date_key", "region", "category"],
)
@dp.expect_or_drop("valid_gold_keys", "store_key IS NOT NULL AND product_key IS NOT NULL AND date_key IS NOT NULL")
@dp.expect_or_drop("valid_gold_measures", "observed_units >= 0 AND estimated_revenue >= 0 AND lost_sales_proxy >= 0")
@dp.expect_or_drop("valid_priority_tier", "priority_tier IN ('low', 'medium', 'high', 'critical')")
def gold_store_product_stockout_daily():
    sales = spark.read.table(f"{SILVER}.fact_sales").alias("sales")
    inventory = spark.read.table(f"{SILVER}.fact_inventory_status").alias("inventory")
    promotion = spark.read.table(f"{SILVER}.fact_promotion").alias("promotion")
    external = spark.read.table(f"{SILVER}.fact_external_signal").alias("external")
    stores = spark.read.table(f"{SILVER}.dim_store").alias("stores")
    products = spark.read.table(f"{SILVER}.dim_product").alias("products")

    joined = (
        sales.join(stores, F.col("sales.store_key") == F.col("stores.store_key"), "inner")
        .join(products, F.col("sales.product_key") == F.col("products.product_key"), "inner")
        .join(
            inventory,
            (F.col("sales.store_key") == F.col("inventory.store_key"))
            & (F.col("sales.product_key") == F.col("inventory.product_key"))
            & (F.col("sales.date_key") == F.col("inventory.date_key")),
            "left",
        )
        .join(
            promotion,
            (F.col("sales.store_key") == F.col("promotion.store_key"))
            & (F.col("sales.product_key") == F.col("promotion.product_key"))
            & (F.col("sales.date_key") == F.col("promotion.date_key")),
            "left",
        )
        .join(
            external,
            (F.col("sales.store_key") == F.col("external.store_key"))
            & (F.col("sales.date_key") == F.col("external.date_key")),
            "left",
        )
    )

    stockout_hours = F.coalesce(F.col("inventory.stockout_hours"), F.lit(0))
    discount_rate = F.coalesce(F.col("promotion.discount_rate"), F.lit(0.0))
    promotion_flag = F.coalesce(F.col("promotion.promotion_flag"), F.lit(False))
    lost_sales_proxy = F.round(F.col("sales.estimated_revenue") * (stockout_hours / F.lit(SERVICE_WINDOW_HOURS)), 2)
    stockout_risk_score = F.round(
        F.least(
            F.lit(1.0),
            (stockout_hours / F.lit(SERVICE_WINDOW_HOURS))
            + F.when(promotion_flag, F.lit(0.15)).otherwise(F.lit(0.0))
            + F.when(F.col("products.replenishment_class") == "seasonal", F.lit(0.10)).otherwise(F.lit(0.0)),
        ),
        4,
    )

    return joined.select(
        F.col("sales.store_key"),
        F.col("sales.product_key"),
        F.col("sales.date_key"),
        F.col("stores.region"),
        F.col("stores.store_format"),
        F.col("products.category"),
        F.col("products.subcategory"),
        F.col("products.replenishment_class"),
        F.col("sales.observed_units"),
        F.col("sales.estimated_revenue"),
        stockout_hours.alias("stockout_hours"),
        (stockout_hours > 0).alias("stockout_flag"),
        promotion_flag.alias("promotion_flag"),
        discount_rate.alias("discount_rate"),
        F.coalesce(F.col("external.is_holiday"), F.lit(False)).alias("is_holiday"),
        F.coalesce(F.col("external.demand_signal_bucket"), F.lit("normal")).alias("demand_signal_bucket"),
        lost_sales_proxy.alias("lost_sales_proxy"),
        stockout_risk_score.alias("stockout_risk_score"),
        F.when((stockout_hours >= 6) | (lost_sales_proxy >= 100), "critical")
        .when((stockout_hours >= 3) | promotion_flag, "high")
        .when(stockout_hours > 0, "medium")
        .otherwise("low")
        .alias("priority_tier"),
        F.current_timestamp().alias("refreshed_at"),
    )
