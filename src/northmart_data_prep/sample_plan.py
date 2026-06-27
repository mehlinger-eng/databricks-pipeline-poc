from __future__ import annotations

import argparse
import json
from datetime import timedelta

from northmart_data_prep.config import ThinSliceConfig
from northmart_data_prep.mapping import (
    NORTHMART_PRODUCT_CATEGORIES,
    NORTHMART_REGIONS,
    REPLENISHMENT_CLASSES,
    product_key,
    store_key,
)


def build_sample_plan(config: ThinSliceConfig) -> dict[str, object]:
    config.validate()

    return {
        "config": config.to_dict(),
        "date_range": {
            "start_date": config.start_date.isoformat(),
            "end_date": (config.start_date + timedelta(days=config.day_count - 1)).isoformat(),
            "day_count": config.day_count,
        },
        "sample_keys": {
            "stores": [store_key(i + 1) for i in range(config.store_count)],
            "products": [product_key(i + 1) for i in range(config.product_count)],
        },
        "synthetic_dimensions": {
            "regions": list(NORTHMART_REGIONS),
            "product_categories": list(NORTHMART_PRODUCT_CATEGORIES),
            "replenishment_classes": list(REPLENISHMENT_CLASSES),
        },
        "outputs": {
            "bronze": [
                "raw_freshretailnet_daily",
                "northmart_store_master",
                "northmart_product_master",
            ],
            "silver": [
                "dim_store",
                "dim_product",
                "dim_date",
                "fact_sales",
                "fact_inventory_status",
                "fact_promotion",
                "fact_external_signal",
            ],
            "gold": ["gold_store_product_stockout_daily"],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the planned NorthMart thin-slice sample configuration."
    )
    parser.add_argument("--stores", type=int, default=ThinSliceConfig.store_count)
    parser.add_argument("--products", type=int, default=ThinSliceConfig.product_count)
    parser.add_argument("--days", type=int, default=ThinSliceConfig.day_count)
    parser.add_argument("--batch-id", default=ThinSliceConfig.batch_id)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ThinSliceConfig(
        store_count=args.stores,
        product_count=args.products,
        day_count=args.days,
        batch_id=args.batch_id,
    )
    print(json.dumps(build_sample_plan(config), indent=2))


if __name__ == "__main__":
    main()

