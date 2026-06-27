# Discovery Profile: NorthMart Outfitters

## Client Snapshot

NorthMart Outfitters is a fictional regional outdoor and lifestyle retailer with 48 stores across Colorado, Utah, Montana, Idaho, and Wyoming. The company sells hiking, camping, fishing, winter sports, apparel, footwear, and seasonal outdoor gear.

NorthMart has a growing ecommerce channel, but store revenue still drives most of the business. Stores are highly exposed to local weather, tourism patterns, outdoor events, and seasonal promotions.

## Discovery Call Summary

NorthMart's leadership believes preventable stockouts are causing missed revenue during high-demand windows. The problem is not simply "low inventory." Demand changes quickly when weather, promotions, weekends, holidays, and local events overlap.

The business has enough data to diagnose the problem, but it is fragmented across point-of-sale, inventory, product, promotion, and planning systems. Teams rely on spreadsheets and manual reconciliation, which means decisions are often made after the opportunity has passed.

## Stakeholders

- Maya Torres, VP of Store Operations: accountable for store execution, stockout reduction, and customer experience.
- Ethan Brooks, Director of Inventory Planning: owns replenishment planning and inventory coverage.
- Priya Shah, Merchandising Analytics Manager: measures promotion effectiveness and category performance.
- Leo Martinez, Data Engineering Lead: owns pipelines, reporting reliability, and data platform modernization.
- Hannah Kim, Data Scientist: explores demand forecasting and store-product risk models.

## Current Pain Points

- Store teams discover stockouts after customers have already left.
- Inventory planners cannot easily separate true demand spikes from data quality issues.
- Promotion reporting arrives too late to influence replenishment.
- Weather and local event signals are not integrated into planning views.
- Product, store, and inventory data use inconsistent identifiers across systems.
- Executives see revenue results, but not the operational causes behind missed sales.

## Business Questions

- Which store-product combinations are most likely to stock out in the next replenishment window?
- Which stockouts caused the largest lost-sales impact?
- Which promotions created demand that inventory planning failed to support?
- Which demand spikes were explained by weather, holidays, or local events?
- Which stores need action today, and what products should planners prioritize?

## Data Landscape

| Source | Example Grain | Business Owner | Notes |
| --- | --- | --- | --- |
| Point-of-sale transactions | Order line | Store Operations | Reliable revenue source, but corrections arrive late. |
| Inventory snapshots | Store-product-day | Inventory Planning | Daily batch export from inventory system. |
| Product catalog | Product | Merchandising | Category and replenishment attributes are inconsistently maintained. |
| Store master | Store | Store Operations | Includes region, format, climate zone, and location. |
| Promotion calendar | Promotion-product-store-date | Merchandising | Not always aligned with POS product hierarchy. |
| Calendar and holidays | Date | Analytics | Needed for seasonality and planning cycles. |
| Weather and events | Location-date | External | Used as demand context, not as a source of truth. |

## Success Metrics

- Reduce high-impact stockout rate.
- Improve forecast accuracy for store-product demand.
- Increase inventory coverage during promotion windows.
- Reduce manual planning report preparation time.
- Identify lost-sales drivers within one business day instead of several days later.

## Constraints and Assumptions

- The learning implementation uses synthetic or public data only.
- Data volumes are intentionally compact for Databricks Free Edition.
- The first version is batch-oriented, not real-time.
- No sensitive customer PII is required.
- ML starts with interpretable baseline models before advanced forecasting.
- Serving starts with SQL marts and dashboards before custom apps.

## Architecture Implications

- The pipeline needs a medallion model so raw operational exports can be preserved while business-ready metrics are conformed.
- Silver tables need strong product, store, date, and promotion keys because most questions cross those domains.
- Gold marts should be organized around decisions, not source systems.
- Data quality checks should focus on the fields that affect stockout, lost-sales, and replenishment decisions.
- ML predictions should be written back into serving tables so planners can consume them with the rest of the metrics.
