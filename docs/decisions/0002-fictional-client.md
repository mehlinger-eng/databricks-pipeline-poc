# 0002: Fictional Client

## Status

Accepted

## Context

The project needs more than a technical scenario. To practice Solutions Architect thinking, the repo should include the kind of business context that would come from a discovery call: company profile, stakeholders, pains, data landscape, constraints, and success metrics.

## Decision

Use **NorthMart Outfitters** as the fictional client.

NorthMart is a regional outdoor and lifestyle retailer with stores across the Mountain West. Its demand is shaped by seasonality, weather, tourism, promotions, and local events.

## Rationale

NorthMart creates a strong learning scenario because:

- Outdoor retail has intuitive seasonal and weather-driven demand.
- Store inventory problems map directly to revenue and customer experience.
- Promotions, product categories, store locations, and external signals create realistic joins.
- The scenario supports analytics, data quality, SQL serving, and lightweight ML.
- The story is easy to explain in a portfolio, interview, or client-facing architecture conversation.

## Consequences

- Data generation should include seasonal products, regional stores, weather-sensitive demand, promotions, stockouts, and lost-sales impact.
- Gold marts should be designed around inventory planning and store operations decisions.
- The first ML use case should focus on demand forecasting or stockout risk, not generic model experimentation.
- Serving should first answer planner and operator questions before adding custom app features.
