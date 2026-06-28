from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from northmart_data_prep.config import ThinSliceConfig


class ValidationError(Exception):
    """Raised when generated thin-slice data fails validation."""


def validate_generated_slice(config: ThinSliceConfig) -> None:
    config.validate()
    output_path = config.output_path

    raw = read_required_csv(output_path / "raw_freshretailnet_daily.csv")
    stores = read_required_csv(output_path / "northmart_store_master.csv")
    products = read_required_csv(output_path / "northmart_product_master.csv")

    expected_raw_rows = config.store_count * config.product_count * config.day_count
    require(len(raw) == expected_raw_rows, f"raw row count expected {expected_raw_rows}, got {len(raw)}")
    require(len(stores) == config.store_count, f"store count expected {config.store_count}, got {len(stores)}")
    require(len(products) == config.product_count, f"product count expected {config.product_count}, got {len(products)}")

    validate_required_columns(
        raw,
        {
            "city_id",
            "store_id",
            "product_id",
            "dt",
            "sale_amount",
            "stock_hour6_22_cnt",
            "discount",
            "holiday_flag",
            "activity_flag",
            "batch_id",
            "batch_seq",
            "ingested_at",
        },
        "raw_freshretailnet_daily",
    )
    validate_required_columns(
        stores,
        {"northmart_store_id", "source_store_id", "store_name", "region", "state", "batch_id", "ingested_at"},
        "northmart_store_master",
    )
    validate_required_columns(
        products,
        {
            "northmart_product_id",
            "source_product_id",
            "product_name",
            "category",
            "replenishment_class",
            "base_unit_price",
            "batch_id",
            "ingested_at",
        },
        "northmart_product_master",
    )

    require_unique(raw, ["store_id", "product_id", "dt"], "raw_freshretailnet_daily")
    require_unique(stores, ["northmart_store_id"], "northmart_store_master")
    require_unique(products, ["northmart_product_id"], "northmart_product_master")

    require((raw["sale_amount"] >= 0).all(), "raw sale_amount must be non-negative")
    require(raw["stock_hour6_22_cnt"].between(0, 17).all(), "stock_hour6_22_cnt must be between 0 and 17")
    require(((raw["discount"] > 0) & (raw["discount"] <= 1)).all(), "discount must be in (0, 1]")
    require(raw["holiday_flag"].isin([0, 1]).all(), "holiday_flag must be 0 or 1")
    require(raw["activity_flag"].isin([0, 1]).all(), "activity_flag must be 0 or 1")
    require((products["base_unit_price"] > 0).all(), "base_unit_price must be positive")

    require(raw["store_id"].nunique() == config.store_count, "raw store cardinality does not match config")
    require(raw["product_id"].nunique() == config.product_count, "raw product cardinality does not match config")
    require(raw["dt"].nunique() == config.day_count, "raw date cardinality does not match config")


def read_required_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ValidationError(f"Missing generated file: {path}")
    return pd.read_csv(path)


def validate_required_columns(df: pd.DataFrame, required_columns: set[str], table_name: str) -> None:
    missing = sorted(required_columns - set(df.columns))
    require(not missing, f"{table_name} missing required columns: {', '.join(missing)}")


def require_unique(df: pd.DataFrame, columns: list[str], table_name: str) -> None:
    duplicate_count = int(df.duplicated(columns).sum())
    require(duplicate_count == 0, f"{table_name} has {duplicate_count} duplicate rows for {columns}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated NorthMart thin-slice files.")
    parser.add_argument("--stores", type=int, default=ThinSliceConfig.store_count)
    parser.add_argument("--products", type=int, default=ThinSliceConfig.product_count)
    parser.add_argument("--days", type=int, default=ThinSliceConfig.day_count)
    parser.add_argument("--batch-id", default=ThinSliceConfig.batch_id)
    parser.add_argument("--output-root", default=ThinSliceConfig.output_root)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = replace(
        ThinSliceConfig(),
        store_count=args.stores,
        product_count=args.products,
        day_count=args.days,
        batch_id=args.batch_id,
        output_root=args.output_root,
    )
    validate_generated_slice(config)
    print(f"Validation passed for {config.output_root}")


if __name__ == "__main__":
    main()
