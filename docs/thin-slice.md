# First Thin Slice

## Goal

Build the smallest useful NorthMart pipeline that proves the end-to-end architecture:

raw source inputs -> bronze tables -> silver conformed entities -> gold stockout mart -> SQL query or dashboard.

The slice should be small enough to run comfortably in Databricks Free Edition and rich enough to support a credible business conversation.

## Scope

Use a compact sample:

- 5 to 10 stores.
- 50 to 100 products.
- About 90 business days.
- Sales or demand observations.
- Inventory or stockout status.
- Promotion flags or discounts.
- Holiday and weather-style demand context.

## Business Outcome

Help NorthMart planners identify which store-product combinations need attention because they show high demand, low inventory coverage, frequent stockout periods, or promotion-driven risk.

## Initial Questions Answered

- Which stores and products had the most stockout exposure?
- What revenue or demand was likely missed during stockout windows?
- Which promotions coincided with unsupported demand spikes?
- Which store-product combinations should planners prioritize next?

## Bronze Inputs

- Raw sales or demand observations.
- Raw inventory or stockout observations.
- Raw promotion or discount signals.
- Raw calendar, holiday, weather, or event context.
- Synthetic NorthMart store and product master data.

Bronze should preserve source shape and add ingestion metadata such as source name, batch identifier, and ingestion timestamp.

## Silver Entities

- `dim_store`
- `dim_product`
- `dim_date`
- `fact_sales`
- `fact_inventory_status`
- `fact_promotion`
- `fact_external_signal`

Silver should enforce types, normalize identifiers, remove duplicates, and align source records to NorthMart store, product, and date keys.

## First Gold Mart

`gold_store_product_stockout_daily`

Suggested grain: one row per store, product, and business date.

Suggested measures:

- Units sold.
- Revenue.
- Discount rate.
- Stockout hours or stockout flag.
- Inventory coverage indicator.
- Promotion flag.
- Weather or event demand signal.
- Lost-sales proxy.
- Stockout risk score placeholder.

## Validation Checks

- Store and product keys are present and valid.
- Sales quantities and revenue are non-negative.
- Stockout hours are within the valid daily range.
- Promotion discounts are within expected bounds.
- Each gold row has exactly one store, product, and business date.

## Later Incremental Extension

After the static slice works, add a replay harness that lands one business date or batch at a time. This will let the same pipeline demonstrate incremental ingestion, late-arriving records, corrections, missing files, and duplicate replay handling.
