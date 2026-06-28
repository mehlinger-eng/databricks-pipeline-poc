from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone

import pandas as pd

from northmart_data_prep.config import ReplayConfig, ThinSliceConfig
from northmart_data_prep.generate import (
    FRESHRETAILNET_COLUMNS,
    add_ingestion_metadata,
    build_product_master,
    build_store_master,
    generate_synthetic_freshretailnet_like,
    hourly_profile,
    hourly_stock_status,
)

RAW_DATASET = "raw_freshretailnet_daily"
STORE_DATASET = "northmart_store_master"
PRODUCT_DATASET = "northmart_product_master"


def generate_replay(thin: ThinSliceConfig, replay: ReplayConfig) -> dict[str, object]:
    """Generate time-ordered replay batches for the daily fact dataset.

    The masters land once. The raw daily dataset is split into a seed plus the
    configured increments, with a final restatement batch carrying the
    late-arriving rows withheld from the seed and corrected versions of a few
    already-published keys.
    """
    thin.validate()
    if replay.seed_days + sum(replay.increment_days) != thin.day_count:
        raise ValueError(
            "Replay windows must cover exactly day_count days: "
            f"{replay.seed_days} + {sum(replay.increment_days)} != {thin.day_count}"
        )

    base = generate_synthetic_freshretailnet_like(thin).copy()
    base["dt_date"] = pd.to_datetime(base["dt"]).dt.date
    base["day_offset"] = base["dt_date"].map(lambda d: (d - thin.start_date).days)

    # Masters reflect the full population, so the store dimension is complete
    # even while a store's earliest facts are still late-arriving.
    store_master = build_store_master(base["store_id"].drop_duplicates().tolist(), thin)
    product_master = build_product_master(base["product_id"].drop_duplicates().tolist(), thin)

    # Late-arriving rows: one store's earliest days are withheld from the seed.
    late_mask = (base["store_id"] == replay.late_store_id) & (
        base["day_offset"] < replay.late_store_days
    )

    seed_mask = (base["day_offset"] < replay.seed_days) & (~late_mask)

    increment_masks = []
    cursor = replay.seed_days
    for window in replay.increment_days:
        increment_masks.append((base["day_offset"] >= cursor) & (base["day_offset"] < cursor + window))
        cursor += window

    # Corrected rows: re-emit already-published keys with boosted demand and a
    # forced stockout so the restatement is visible downstream.
    correction_mask = (
        (base["store_id"] == replay.correction_store_id)
        & (base["product_id"].isin(replay.correction_product_ids))
        & (base["day_offset"].isin(replay.correction_day_offsets))
    )
    corrected = base[correction_mask].copy()
    corrected["sale_amount"] = (corrected["sale_amount"] * 2.0).round(4)
    corrected["stock_hour6_22_cnt"] = 8
    corrected["activity_flag"] = 1
    corrected["discount"] = 0.85
    corrected["hours_sale"] = corrected["sale_amount"].map(hourly_profile)
    corrected["hours_stock_status"] = corrected["stock_hour6_22_cnt"].map(hourly_stock_status)

    batch_ids = [batch_id for batch_id, _ in replay.batches]
    batch_seqs = {batch_id: seq for batch_id, seq in replay.batches}
    if len(batch_ids) != 2 + len(replay.increment_days):
        raise ValueError("ReplayConfig.batches must define seed + increments + restatement")

    seed_id, *increment_ids, restatement_id = batch_ids

    batch_frames: dict[str, pd.DataFrame] = {seed_id: base[seed_mask]}
    for batch_id, mask in zip(increment_ids, increment_masks):
        batch_frames[batch_id] = base[mask]
    batch_frames[restatement_id] = pd.concat([base[late_mask], corrected], ignore_index=True)

    output_path = replay.output_path
    if output_path.exists():
        shutil.rmtree(output_path)
    raw_dir = output_path / RAW_DATASET
    raw_dir.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    manifest_batches = []
    for index, batch_id in enumerate(batch_ids):
        frame = batch_frames[batch_id][FRESHRETAILNET_COLUMNS]
        enriched = add_ingestion_metadata(
            frame,
            thin,
            batch_id=batch_id,
            batch_seq=batch_seqs[batch_id],
            ingested_at=base_time + timedelta(hours=index),
        )
        file_path = raw_dir / f"{batch_id}.csv"
        enriched.to_csv(file_path, index=False)
        manifest_batches.append(
            {
                "batch_id": batch_id,
                "batch_seq": batch_seqs[batch_id],
                "rows": int(len(enriched)),
                "file": str(file_path),
            }
        )

    store_dir = output_path / STORE_DATASET
    store_dir.mkdir(parents=True, exist_ok=True)
    store_master.to_csv(store_dir / f"{STORE_DATASET}.csv", index=False)

    product_dir = output_path / PRODUCT_DATASET
    product_dir.mkdir(parents=True, exist_ok=True)
    product_master.to_csv(product_dir / f"{PRODUCT_DATASET}.csv", index=False)

    raw_batch_total = sum(b["rows"] for b in manifest_batches)
    distinct_grain = int(base[["store_id", "product_id", "dt"]].drop_duplicates().shape[0])

    return {
        "output_root": str(output_path),
        "stores": int(len(store_master)),
        "products": int(len(product_master)),
        "batches": manifest_batches,
        "expectations": {
            "raw_rows_landed_total": raw_batch_total,
            "corrected_rows": int(len(corrected)),
            "late_arriving_rows": int(late_mask.sum()),
            "silver_fact_rows_after_full_replay": distinct_grain,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate NorthMart incremental replay batches.")
    parser.add_argument("--output-root", default=ReplayConfig.output_root)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from dataclasses import replace

    replay = replace(ReplayConfig(), output_root=args.output_root)
    manifest = generate_replay(ThinSliceConfig(), replay)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
