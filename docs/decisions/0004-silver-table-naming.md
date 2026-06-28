# 0004: Silver Table Naming

## Status

Accepted

## Context

The first PySpark Lakeflow pipeline creates conformed tables named `dim_store`, `dim_product`, `fact_sales`, and related facts. These tables currently live conceptually in the silver layer.

There was a concern that `dim_` and `fact_` names might imply gold or presentation-layer ownership.

## Decision

Keep `dim_` and `fact_` names for analyst-ready silver tables.

NorthMart uses medallion schemas plus modeling-role table names:

```text
<catalog>.bronze.<source-shaped-table>
<catalog>.silver.dim_store
<catalog>.silver.dim_product
<catalog>.silver.fact_sales
<catalog>.gold.gold_store_product_stockout_daily
```

The schema communicates the medallion layer. The table prefix communicates the analytical role.

## Rationale

This convention keeps the model useful for analysts while preserving medallion clarity:

- Silver tables are trusted, conformed, quality-checked, and queryable by analysts.
- `dim_` tables represent descriptive entities.
- `fact_` tables represent measurable events or observations.
- Gold tables are curated decision products, marts, dashboards, and model-serving outputs.

Renaming silver tables to `silver_*` would reduce ambiguity, but it would also make analyst-facing table names less natural and more redundant inside a `silver` schema.

## Consequences

- Documentation must clearly explain that silver is analyst-ready, not hidden or internal-only.
- Business dashboards should prefer gold marts unless analysts need flexible exploration over conformed data.
- Future gold dimensional models can still use `gold_dim_*` or `gold_fact_*` names if we intentionally create a presentation-layer star schema.
