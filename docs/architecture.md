# Architecture Notes

## Data Sources

Use a hybrid sourcing strategy. NorthMart-specific master data and business events are simulated, while demand and stockout behavior can be anchored by a compact public retail dataset sample.

- Sales transactions: order line grain with timestamp, store, product, quantity, and revenue.
- Inventory snapshots: daily store-product on-hand quantity.
- Product catalog: category, brand, price, shelf life, and replenishment class.
- Store dimension: geography, format, region, and local demographics.
- Promotions: promotion windows, discount depth, and product coverage.
- Calendar: holidays, weekdays, paydays, and seasonal flags.
- Weather or events: external demand signals by location and date.

The first public dataset candidate is FreshRetailNet-50K because it includes sales, stockout annotations, discounts, holidays, and weather covariates. Walmart M5 remains a fallback for classic sales forecasting, but it is not the first choice because it lacks explicit stockout status.

## Medallion Layers

### Bronze

Raw files and landing tables. Keep the original shape, add ingestion metadata, and preserve enough detail to replay transformations.

### Silver

Cleaned and conformed entities:

- `dim_store`
- `dim_product`
- `fact_sales`
- `fact_inventory_snapshot`
- `fact_promotion`
- `dim_calendar`
- `fact_external_signal`

Typical work includes schema enforcement, deduplication, type normalization, valid key checks, and late-arriving data handling.

### Gold

Business-ready serving tables:

- Daily sales by store and product.
- Inventory coverage and stockout indicators.
- Promotion performance.
- Lost sales estimates.
- Store-product demand features.
- Stockout risk predictions.

## Serving Surfaces

Start with SQL marts and an AI/BI dashboard. Add a Databricks App only when we need custom interactivity, write-back, workflow actions, or an embedded assistant.

## ML Scope

Start lightweight:

- Baseline demand forecast by store-product-day.
- Stockout risk classification.
- Anomaly detection for unexpected demand spikes.

The first version should emphasize explainability and integration into the lakehouse over model complexity.

## Databricks Free Edition Constraints

- Keep datasets compact but realistic.
- Prefer serverless compute.
- Avoid GPU-dependent models.
- Keep jobs small and avoid unnecessary parallel task fanout.
- Design the first pipeline as a thin vertical slice before expanding breadth.

## Incremental Strategy

Start with a static 90-day slice. Add incremental behavior later through a replay harness that lands one `run_date` or `batch_id` at a time into raw volume paths, then re-runs the same bronze, silver, and gold logic.
