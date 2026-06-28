# Source Mapping

## Purpose

This document defines how the first NorthMart thin slice maps public FreshRetailNet-50K fields and synthetic NorthMart fields into the medallion model.

FreshRetailNet-50K is a behavioral anchor. It is not treated as literal NorthMart operational data. NorthMart-specific business identity, product naming, store geography, and planning attributes are simulated.

## Mapping Principles

- Preserve raw source fields in bronze.
- Create stable NorthMart business keys in silver.
- Use `dim_` and `fact_` names in silver when they describe analyst-ready conformed dimensions and facts.
- Do not expose encoded public source identifiers directly in gold unless needed for debugging.
- Treat FreshRetailNet sales values as normalized demand signals, not literal dollars.
- Derive NorthMart estimated revenue from normalized demand and synthetic product pricing.
- Defer incremental replay fields until after the static thin slice works.

Silver is queryable by analysts. Gold is the preferred layer for curated dashboards, decision marts, and stakeholder-facing outputs.

## Public Source Fields

| FreshRetailNet Field | Bronze Use | Silver/Gold Interpretation |
| --- | --- | --- |
| `city_id` | Preserve source geography. | Used to distribute sampled stores across NorthMart regions if needed. |
| `store_id` | Preserve source store identifier. | Mapped to `store_key` through synthetic NorthMart store master. |
| `management_group_id` | Preserve source hierarchy. | Optional input to NorthMart category mapping. |
| `first_category_id` | Preserve source hierarchy. | Optional input to NorthMart category mapping. |
| `second_category_id` | Preserve source hierarchy. | Optional input to NorthMart subcategory mapping. |
| `third_category_id` | Preserve source hierarchy. | Optional input to NorthMart subcategory mapping. |
| `product_id` | Preserve source product identifier. | Mapped to `product_key` through synthetic NorthMart product master. |
| `dt` | Source business date. | Becomes `date_key`. |
| `sale_amount` | Normalized source sales amount. | Used as `normalized_sales_amount` and to derive `observed_units`. |
| `hours_sale` | Optional hourly profile. | Deferred for first daily mart; useful later for intraday analysis. |
| `stock_hour6_22_cnt` | Daily stockout-hour count. | Becomes `stockout_hours`. |
| `hours_stock_status` | Optional hourly stockout profile. | Deferred for first daily mart; useful later for replay or intraday stockout analysis. |
| `discount` | Source remaining-price multiplier. | Converted to `discount_rate = 1 - discount`. |
| `holiday_flag` | Source holiday indicator. | Becomes `is_holiday`. |
| `activity_flag` | Source promotion/activity indicator. | Becomes `promotion_flag` and helps assign synthetic campaigns. |
| `precpt` | Weather covariate. | Becomes `precipitation`. |
| `avg_temperature` | Weather covariate. | Preserved as average temperature. |
| `avg_humidity` | Weather covariate. | Preserved as average humidity. |
| `avg_wind_level` | Weather covariate. | Preserved as average wind level. |

## Simulated NorthMart Fields

| Field Group | Examples | Why Simulated |
| --- | --- | --- |
| Store identity | `store_key`, `store_name`, `region`, `state`, `city`, `store_format`, `climate_zone` | The public source has encoded stores, but NorthMart needs explainable store geography and operating segments. |
| Product identity | `product_key`, `product_name`, `category`, `subcategory`, `brand`, `replenishment_class`, `base_unit_price`, `seasonal_peak` | The public source has encoded product categories, but NorthMart needs outdoor retail categories and pricing. |
| Promotion context | `campaign_name`, promotion themes | The public source has activity and discount signals, but NorthMart needs business-readable campaigns. |
| Planning attributes | `inventory_coverage_status`, `priority_tier`, `lost_sales_proxy`, `stockout_risk_score` | These are decision-support fields created by the lakehouse pipeline. |

## Key Mapping

Initial key mapping can be deterministic:

- `store_key = NM-STORE-` plus a zero-padded sequence assigned to sampled source stores.
- `product_key = NM-SKU-` plus a zero-padded sequence assigned to sampled source products.
- `date_key = dt`.

The mapping should be stored as synthetic master data so facts can join consistently across runs.

## First Gold Mart Derivations

Suggested first-pass derivations:

- `observed_units`: scaled value derived from normalized source `sale_amount`.
- `estimated_revenue`: `observed_units * base_unit_price * (1 - discount_rate)`.
- `stockout_flag`: `stockout_hours > 0`.
- `discount_rate`: `1 - discount`.
- `promotion_flag`: `activity_flag = 1 or discount_rate > 0`.
- `lost_sales_proxy`: positive estimate when stockout hours occur during high observed demand.
- `priority_tier`: rules-based tier using stockout hours, lost-sales proxy, promotion flag, and replenishment class.
- `stockout_risk_score`: optional rules-based placeholder until ML is introduced.

## Deferred Until Later

- Full hourly grain.
- Replay-based incremental batches.
- Late-arriving source corrections.
- Public weather API ingestion.
- Model-trained stockout risk scores.
