# NorthMart Data Prep

Utilities for planning, generating, and validating the first NorthMart thin-slice dataset.

The generator creates bronze-compatible local files for the first static slice:

- `raw_freshretailnet_daily.csv`
- `northmart_store_master.csv`
- `northmart_product_master.csv`

Generated files are written under `data/generated/northmart_thin_slice/`, which is ignored by git.

## Install Dependencies

From the repository root:

```bash
python3 -m pip install -r requirements.txt
```

## Preview The Slice Plan

```bash
PYTHONPATH=src python3 -m northmart_data_prep.sample_plan
```

## Generate The Default Synthetic Slice

Use this fast local path first. It creates deterministic FreshRetailNet-like behavior without downloading the public dataset.

```bash
PYTHONPATH=src python3 -m northmart_data_prep.generate --source synthetic
```

## Validate Generated Files

```bash
PYTHONPATH=src python3 -m northmart_data_prep.validate
```

## FreshRetailNet Sampling

FreshRetailNet-50K is the intended public-source anchor. Use this when you want to sample the real public dataset instead of the deterministic synthetic fallback:

```bash
PYTHONPATH=src python3 -m northmart_data_prep.generate --source freshretailnet
```

This may download data from Hugging Face and can take longer than the synthetic path.

## Override Slice Size

Keep overrides within the Phase 1 guardrails:

```bash
PYTHONPATH=src python3 -m northmart_data_prep.generate --source synthetic --stores 8 --products 80 --days 90
```

## Replay Batches (Incremental)

To exercise incremental ingestion, late-arriving records, and corrected records,
generate the slice as time-ordered batches instead of a single file:

```bash
PYTHONPATH=src python3 -m northmart_data_prep.replay
```

This writes a seed (60 days), two 15-day increments, and a restatement batch
(late-arriving + corrected rows) under `data/generated/northmart_replay/`, each
stamped with a monotonic `batch_seq`. The end-to-end Databricks demonstration is
orchestrated by `databricks/scripts/run_replay.sh` and documented in
[docs/databricks-incremental-replay.md](../../docs/databricks-incremental-replay.md).

