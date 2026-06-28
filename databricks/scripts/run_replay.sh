#!/usr/bin/env bash
#
# Replay harness for the NorthMart medallion pipeline.
#
# Demonstrates incremental ingestion on Databricks Free Edition by landing the
# 90-day slice as time-ordered batches and re-running the pipeline between
# batches. Auto Loader ingests only newly landed files each run; silver applies
# latest-wins so the final restatement batch reconciles late-arriving and
# corrected records.
#
# Stages:
#   1. seed         (60 days, full-refresh to reset checkpoints/tables)
#   2. replay-002   (+15 days, incremental)
#   3. replay-003   (+15 days, incremental)
#   4. restatement  (late-arriving + corrected rows, incremental)
#
# Usage: databricks/scripts/run_replay.sh
# Env overrides: PROFILE, TARGET, WAREHOUSE_ID, CATALOG, PIPELINE, OUTPUT_ROOT

set -euo pipefail

PROFILE="${PROFILE:-DEFAULT}"
TARGET="${TARGET:-dev}"
WAREHOUSE_ID="${WAREHOUSE_ID:-68492bc2dc184d9a}"
CATALOG="${CATALOG:-northmart}"
PIPELINE="${PIPELINE:-northmart_bronze_pipeline}"
OUTPUT_ROOT="${OUTPUT_ROOT:-data/generated/northmart_replay}"

LANDING="dbfs:/Volumes/${CATALOG}/bronze/landing/northmart_thin_slice"
RAW_DS="raw_freshretailnet_daily"
STORE_DS="northmart_store_master"
PRODUCT_DS="northmart_product_master"

SEED_BATCH="replay-001-seed"
INCREMENT_BATCHES=("replay-002-inc" "replay-003-inc")
RESTATEMENT_BATCH="replay-004-restatement"

run_sql() {
  databricks api post /api/2.0/sql/statements --profile "$PROFILE" --json \
    "{\"warehouse_id\":\"$WAREHOUSE_ID\",\"statement\":\"$1\",\"wait_timeout\":\"50s\"}" 2>&1 |
    python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('status',{}); print('  state:',s.get('state'), s.get('error','')); [print('  ', ' | '.join('' if c is None else str(c) for c in r)) for r in (d.get('result',{}).get('data_array') or [])]"
}

verify_progress() {
  echo "--- verify: $1 ---"
  run_sql "SELECT 'bronze_landed' k, cast(count(*) AS string) v FROM ${CATALOG}.bronze.bronze_raw_freshretailnet_daily UNION ALL SELECT 'silver_fact_sales', cast(count(*) AS string) FROM ${CATALOG}.silver.fact_sales UNION ALL SELECT 'gold_rows', cast(count(*) AS string) FROM ${CATALOG}.gold.gold_store_product_stockout_daily UNION ALL SELECT 'gold_max_date', cast(max(date_key) AS string) FROM ${CATALOG}.gold.gold_store_product_stockout_daily"
}

upload_batch() {
  local file="$1"
  echo "  uploading $file"
  databricks fs cp "$OUTPUT_ROOT/$RAW_DS/$file.csv" "$LANDING/$RAW_DS/$file.csv" --overwrite --profile "$PROFILE"
}

echo "=== Step 1: generate replay batches locally ==="
PYTHONPATH=src python3 -m northmart_data_prep.replay --output-root "$OUTPUT_ROOT"

echo "=== Step 2: reset landing folder ==="
databricks fs rm "$LANDING/$RAW_DS" --recursive --profile "$PROFILE" 2>/dev/null || true
databricks fs rm "$LANDING/$STORE_DS" --recursive --profile "$PROFILE" 2>/dev/null || true
databricks fs rm "$LANDING/$PRODUCT_DS" --recursive --profile "$PROFILE" 2>/dev/null || true
for ds in "$RAW_DS" "$STORE_DS" "$PRODUCT_DS"; do
  databricks fs mkdir "$LANDING/$ds" --profile "$PROFILE"
done

echo "=== Step 3: land masters + seed batch ==="
databricks fs cp "$OUTPUT_ROOT/$STORE_DS/$STORE_DS.csv" "$LANDING/$STORE_DS/$STORE_DS.csv" --overwrite --profile "$PROFILE"
databricks fs cp "$OUTPUT_ROOT/$PRODUCT_DS/$PRODUCT_DS.csv" "$LANDING/$PRODUCT_DS/$PRODUCT_DS.csv" --overwrite --profile "$PROFILE"
upload_batch "$SEED_BATCH"

echo "=== Step 4: full-refresh run (reset state, ingest seed) ==="
databricks bundle run "$PIPELINE" -t "$TARGET" --profile "$PROFILE" --full-refresh-all 2>&1 | tail -3
verify_progress "after seed (expect bronze=37200, gold max date 2024-04-29)"

for batch in "${INCREMENT_BATCHES[@]}"; do
  echo "=== Increment: $batch ==="
  upload_batch "$batch"
  databricks bundle run "$PIPELINE" -t "$TARGET" --profile "$PROFILE" 2>&1 | tail -3
  verify_progress "after $batch"
done

echo "=== Restatement: $RESTATEMENT_BATCH (late-arriving + corrected) ==="
upload_batch "$RESTATEMENT_BATCH"
databricks bundle run "$PIPELINE" -t "$TARGET" --profile "$PROFILE" 2>&1 | tail -3
verify_progress "after restatement (expect bronze=57615, silver/gold=57600)"

echo "=== Provenance: rows landed per batch in bronze ==="
run_sql "SELECT batch_id, count(*) rows FROM ${CATALOG}.bronze.bronze_raw_freshretailnet_daily GROUP BY batch_id ORDER BY batch_id"

echo "=== Late-arriving check: NM-STORE-008 earliest dates now present in gold ==="
run_sql "SELECT count(*) late_store_early_rows FROM ${CATALOG}.gold.gold_store_product_stockout_daily WHERE store_key='NM-STORE-008' AND date_key < '2024-03-16'"

echo "=== Restatement check: corrected keys now show forced stockout in gold ==="
run_sql "SELECT store_key, product_key, date_key, stockout_hours, round(estimated_revenue,2) rev, round(lost_sales_proxy,2) lost, priority_tier FROM ${CATALOG}.gold.gold_store_product_stockout_daily WHERE store_key='NM-STORE-001' AND product_key='NM-SKU-00001' AND date_key IN ('2024-03-06','2024-03-07','2024-03-08') ORDER BY date_key"

echo "=== Replay complete ==="
