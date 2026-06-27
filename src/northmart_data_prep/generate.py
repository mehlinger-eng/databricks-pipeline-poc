from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import random

import pandas as pd

from northmart_data_prep.config import ThinSliceConfig
from northmart_data_prep.mapping import (
    BRANDS,
    NORTHMART_PRODUCT_CATEGORIES,
    NORTHMART_STATES,
    REPLENISHMENT_CLASSES,
    SEASONAL_PEAKS,
    STORE_FORMATS,
    product_key,
    store_key,
)


FRESHRETAILNET_COLUMNS = [
    "city_id",
    "store_id",
    "management_group_id",
    "first_category_id",
    "second_category_id",
    "third_category_id",
    "product_id",
    "dt",
    "sale_amount",
    "hours_sale",
    "stock_hour6_22_cnt",
    "hours_stock_status",
    "discount",
    "holiday_flag",
    "activity_flag",
    "precpt",
    "avg_temperature",
    "avg_humidity",
    "avg_wind_level",
]


def generate_thin_slice(config: ThinSliceConfig, source: str = "synthetic") -> dict[str, Path]:
    config.validate()
    output_path = config.output_path
    output_path.mkdir(parents=True, exist_ok=True)

    if source == "freshretailnet":
        raw_df = sample_freshretailnet(config)
    elif source == "synthetic":
        raw_df = generate_synthetic_freshretailnet_like(config)
    else:
        raise ValueError("source must be either 'synthetic' or 'freshretailnet'")

    raw_df = add_ingestion_metadata(raw_df, config)
    store_master = build_store_master(raw_df["store_id"].drop_duplicates().tolist(), config)
    product_master = build_product_master(raw_df["product_id"].drop_duplicates().tolist(), config)

    outputs = {
        "raw_freshretailnet_daily": output_path / "raw_freshretailnet_daily.csv",
        "northmart_store_master": output_path / "northmart_store_master.csv",
        "northmart_product_master": output_path / "northmart_product_master.csv",
    }

    raw_df.to_csv(outputs["raw_freshretailnet_daily"], index=False)
    store_master.to_csv(outputs["northmart_store_master"], index=False)
    product_master.to_csv(outputs["northmart_product_master"], index=False)

    return outputs


def sample_freshretailnet(config: ThinSliceConfig) -> pd.DataFrame:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError(
            "The 'datasets' package is required for FreshRetailNet sampling. "
            "Install dependencies with `python3 -m pip install -r requirements.txt`."
        ) from exc

    end_date = config.start_date + timedelta(days=config.day_count - 1)
    dataset = load_dataset(
        config.source_dataset,
        split=config.source_split,
        streaming=True,
    )

    selected_stores: list[int] = []
    selected_products: list[int] = []
    rows: list[dict[str, object]] = []
    target_rows = config.store_count * config.product_count * config.day_count

    for row in dataset:
        row_date = date.fromisoformat(str(row["dt"]))
        if row_date < config.start_date or row_date > end_date:
            continue

        source_store_id = int(row["store_id"])
        source_product_id = int(row["product_id"])

        if source_store_id not in selected_stores and len(selected_stores) < config.store_count:
            selected_stores.append(source_store_id)
        if source_product_id not in selected_products and len(selected_products) < config.product_count:
            selected_products.append(source_product_id)

        if source_store_id in selected_stores and source_product_id in selected_products:
            rows.append({column: row[column] for column in FRESHRETAILNET_COLUMNS})

        if len(rows) >= target_rows:
            break

    if not rows:
        raise RuntimeError("FreshRetailNet sampling returned no rows for the configured date window")

    return pd.DataFrame(rows)


def generate_synthetic_freshretailnet_like(config: ThinSliceConfig) -> pd.DataFrame:
    rng = random.Random(42)
    dates = [config.start_date + timedelta(days=offset) for offset in range(config.day_count)]
    rows: list[dict[str, object]] = []

    for store_idx in range(config.store_count):
        source_store_id = 10_000 + store_idx
        city_id = 100 + (store_idx % 5)
        for product_idx in range(config.product_count):
            source_product_id = 50_000 + product_idx
            category_seed = product_idx % len(NORTHMART_PRODUCT_CATEGORIES)
            baseline = 2.0 + (product_idx % 12) * 0.4 + (store_idx % 3) * 0.6
            for current_date in dates:
                weekend_lift = 1.25 if current_date.weekday() >= 5 else 1.0
                seasonal_lift = 1.35 if current_date.month in (3, 4, 5) and category_seed in (0, 1, 7) else 1.0
                activity_flag = 1 if (product_idx + current_date.toordinal()) % 17 == 0 else 0
                holiday_flag = 1 if current_date.day in (1, 15) and current_date.weekday() >= 4 else 0
                discount = 0.85 if activity_flag else 1.0
                weather_shock = 1.2 if (store_idx + current_date.day) % 19 == 0 else 1.0
                sale_amount = round(
                    max(0.0, baseline * weekend_lift * seasonal_lift * weather_shock * rng.uniform(0.75, 1.35)),
                    4,
                )
                stockout_hours = stockout_hours_for(sale_amount, activity_flag, rng)
                rows.append(
                    {
                        "city_id": city_id,
                        "store_id": source_store_id,
                        "management_group_id": category_seed + 1,
                        "first_category_id": category_seed + 10,
                        "second_category_id": category_seed + 100,
                        "third_category_id": category_seed + 1000,
                        "product_id": source_product_id,
                        "dt": current_date.isoformat(),
                        "sale_amount": sale_amount,
                        "hours_sale": hourly_profile(sale_amount),
                        "stock_hour6_22_cnt": stockout_hours,
                        "hours_stock_status": hourly_stock_status(stockout_hours),
                        "discount": discount,
                        "holiday_flag": holiday_flag,
                        "activity_flag": activity_flag,
                        "precpt": round(max(0.0, rng.gauss(0.08, 0.12)), 4),
                        "avg_temperature": round(rng.uniform(35.0, 72.0), 2),
                        "avg_humidity": round(rng.uniform(25.0, 75.0), 2),
                        "avg_wind_level": round(rng.uniform(1.0, 8.0), 2),
                    }
                )

    return pd.DataFrame(rows)


def stockout_hours_for(sale_amount: float, activity_flag: int, rng: random.Random) -> int:
    if sale_amount < 4 and not activity_flag:
        return 0
    stockout_probability = min(0.55, 0.04 + sale_amount / 45 + activity_flag * 0.12)
    if rng.random() > stockout_probability:
        return 0
    return rng.randint(1, 8)


def hourly_profile(daily_amount: float) -> list[float]:
    weights = [0.02] * 6 + [0.04, 0.05, 0.08, 0.08, 0.06, 0.05, 0.04, 0.04, 0.05, 0.07, 0.08, 0.08, 0.07, 0.05, 0.04, 0.03, 0.02, 0.02]
    total = sum(weights)
    return [round(daily_amount * weight / total, 4) for weight in weights]


def hourly_stock_status(stockout_hours: int) -> list[int]:
    status = [0] * 24
    for hour in range(22 - stockout_hours, 22):
        if 0 <= hour < 24:
            status[hour] = 1
    return status


def add_ingestion_metadata(raw_df: pd.DataFrame, config: ThinSliceConfig) -> pd.DataFrame:
    enriched = raw_df.copy()
    enriched["dt"] = pd.to_datetime(enriched["dt"]).dt.date
    enriched["source_dataset"] = config.source_dataset
    enriched["source_split"] = config.source_split
    enriched["batch_id"] = config.batch_id
    enriched["ingested_at"] = datetime.now(timezone.utc)
    return enriched


def build_store_master(source_store_ids: Iterable[int], config: ThinSliceConfig) -> pd.DataFrame:
    rows = []
    ingested_at = datetime.now(timezone.utc)
    for idx, source_store_id in enumerate(sorted(source_store_ids), start=1):
        state_name, state_code, region, climate_zone = NORTHMART_STATES[(idx - 1) % len(NORTHMART_STATES)]
        rows.append(
            {
                "northmart_store_id": store_key(idx),
                "source_store_id": source_store_id,
                "store_name": f"NorthMart {state_code}-{idx:02d}",
                "region": region,
                "state": state_name,
                "city": f"{state_name} Market {idx}",
                "store_format": STORE_FORMATS[(idx - 1) % len(STORE_FORMATS)],
                "climate_zone": climate_zone,
                "opened_date": date(2015 + (idx % 7), ((idx - 1) % 12) + 1, 1),
                "batch_id": config.batch_id,
                "ingested_at": ingested_at,
            }
        )
    return pd.DataFrame(rows)


def build_product_master(source_product_ids: Iterable[int], config: ThinSliceConfig) -> pd.DataFrame:
    rows = []
    ingested_at = datetime.now(timezone.utc)
    for idx, source_product_id in enumerate(sorted(source_product_ids), start=1):
        category = NORTHMART_PRODUCT_CATEGORIES[(idx - 1) % len(NORTHMART_PRODUCT_CATEGORIES)]
        rows.append(
            {
                "northmart_product_id": product_key(idx),
                "source_product_id": source_product_id,
                "product_name": f"{category} Product {idx:03d}",
                "category": category,
                "subcategory": f"{category} Core",
                "brand": BRANDS[(idx - 1) % len(BRANDS)],
                "replenishment_class": REPLENISHMENT_CLASSES[(idx - 1) % len(REPLENISHMENT_CLASSES)],
                "base_unit_price": round(12.99 + (idx % 40) * 2.75, 2),
                "seasonal_peak": SEASONAL_PEAKS[(idx - 1) % len(SEASONAL_PEAKS)],
                "batch_id": config.batch_id,
                "ingested_at": ingested_at,
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local NorthMart bronze-compatible thin-slice files.")
    parser.add_argument("--source", choices=("synthetic", "freshretailnet"), default="synthetic")
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
    outputs = generate_thin_slice(config, source=args.source)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
