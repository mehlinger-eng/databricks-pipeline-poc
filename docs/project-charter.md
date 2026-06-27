# Project Charter

## Working Title

NorthMart Retail Lakehouse Intelligence

## Client

NorthMart Outfitters, a fictional regional outdoor and lifestyle retailer.

## One-Line Pitch

Build a Databricks lakehouse that turns NorthMart's fragmented retail operations data into demand, inventory, and stockout-risk intelligence.

## Business Problem

NorthMart planners need to prevent stockouts before they happen, but the signals are fragmented across sales transactions, inventory snapshots, product catalogs, promotions, store metadata, holidays, weather, and local events.

The learning project should show how a lakehouse architecture creates a trusted analytical foundation and then serves decision-ready insights.

## Success Criteria

- A reproducible data-generation or ingestion path exists.
- Bronze, silver, and gold layers are visible and explainable.
- Gold tables answer real planning questions.
- A dashboard or app surfaces KPIs and drilldowns.
- At least one ML output is produced, stored, and served back into the lakehouse.
- The design stays realistic for Databricks Free Edition.

## Core Metrics

- Revenue.
- Lost sales estimate.
- Stockout rate.
- Forecast error.
- Inventory coverage days.
- Promotion lift.
- Store-product risk score.

## Primary Decisions Supported

- Which stores need replenishment attention?
- Which products are chronically understocked?
- Which promotions caused demand spikes?
- Which demand patterns are seasonal, local, or anomalous?
- Which store-product combinations are likely to stock out soon?
