# Serving: AI/BI Stockout Dashboard

This document describes the Phase 3 serving layer: a Databricks AI/BI (Lakeview)
dashboard built on the gold stockout mart, shipped as a version-controlled
`.lvdash.json` and deployed through the Asset Bundle.

It builds on [databricks-deploy-run.md](databricks-deploy-run.md) and
[databricks-incremental-replay.md](databricks-incremental-replay.md).

## What It Serves

The dashboard turns `northmart.gold.gold_store_product_stockout_daily` into a
planner-facing view answering the gold mart's business questions: where is
stockout exposure concentrated, and where should inventory planners focus before
the next replenishment cycle?

- **Dashboard JSON:** [sql/dashboards/northmart_stockout_overview.lvdash.json](../sql/dashboards/northmart_stockout_overview.lvdash.json)
- **Bundle resource:** [databricks/workflows/northmart_dashboard.yml](../databricks/workflows/northmart_dashboard.yml)
- **Warehouse:** serverless `${var.warehouse_id}` (Serverless Starter Warehouse)

## Layout

Single overview page (12-column `GRID_V1`) plus a global filters page:

| Section | Widgets |
| --- | --- |
| KPIs | Total lost-sales proxy, stockout rate (%), critical-tier row count |
| Where is the exposure? | Lost-sales proxy by region (bar), by category (bar) |
| Trend and priority mix | Daily lost-sales proxy (line), rows by priority tier (bar) |
| Top offenders | Top 50 store-product-day rows by lost-sales proxy (table) |
| Filters page | Multi-select: region, category, priority tier |

## Dataset Design

Two datasets back the dashboard:

- **`ds_mart`** - row-level projection of the gold mart with two derived integer
  helpers (`stockout_int`, `critical_int`) so widget-level aggregations
  (`SUM`/`AVG`) work. The KPIs and all four charts read from this single shared
  dataset, so the global filters (region, category, priority tier) cascade to
  every one of them.
- **`ds_top_offenders`** - a pre-sorted `ORDER BY lost_sales_proxy DESC LIMIT 50`
  projection (critical/high only) for the detail table. This is a global top-50
  reference and is intentionally not cross-filtered.

All queries use fully-qualified `northmart.gold.*` names and were tested via the
SQL Statements API before being embedded in the dashboard JSON, per the
`databricks-aibi-dashboards` skill's mandatory-validation workflow.

## Deploy

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy   -t dev --profile DEFAULT
```

The dashboard is created/updated in place by the deploy (no `bundle run`
needed). Confirm via:

```bash
databricks bundle summary -t dev --profile DEFAULT   # prints the dashboard URL
databricks api get /api/2.0/lakeview/dashboards/<id> --profile DEFAULT
```

## Verification

After deploy, the dashboard registered `ACTIVE` with both datasets, 13 overview
widgets, and 3 filter widgets. The six dataset queries were validated against the
live gold mart, returning (current replay state):

- Total lost-sales proxy ~= 11.1M; stockout rate ~= 15.8%; critical rows = 8,885.
- Regional exposure ranks Northern Plains > Rockies > Wasatch > High Desert.
- Category exposure leads with Hydration and Camping.
- 90 daily trend points; 50 top-offender rows (Hydration/Camping SKUs dominate).

A visual render check in the browser requires an authenticated Databricks
session; open the dashboard URL from `databricks bundle summary` to confirm
widgets render.

## What a Planner Reads From It (SA view)

- **Headline exposure:** the lost-sales proxy KPI quantifies revenue at risk from
  stockouts, turning an operational metric into a dollar-framed business signal.
- **Where to act:** region and category bars point planners at the highest-impact
  buckets (Northern Plains; Hydration/Camping) for the next replenishment cycle.
- **What to fix first:** the priority-tier mix and top-offenders table surface the
  specific store-product-day combinations in `critical`/`high` tiers.

## Notes / Gotchas

- AI/BI dashboards are supported on Free Edition and backed by the serverless SQL
  warehouse.
- Widget contract: the `name` in `query.fields` must exactly match the
  `fieldName` in `encodings`, or widgets show "no selected fields to visualize".
- The `dev` bundle target prefixes the dashboard display name with
  `[dev <user>]`; this is expected in development mode.
- Future enhancement: cross-filter the top-offenders table and add a Genie space
  for natural-language Q&A over the mart.
