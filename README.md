# NorthMart Retail Lakehouse Intelligence

A Databricks Free Edition learning project that builds a realistic retail demand and inventory intelligence platform for **NorthMart Outfitters**, a fictional regional outdoor and lifestyle retailer.

The goal is to practice modern data engineering end to end: ingestion, medallion transformations, data quality, SQL serving, dashboards, and lightweight ML. The project is intentionally business-oriented so the technical work maps to a clear Solutions Architect story.

## Business Story

NorthMart Outfitters is losing revenue because stores experience preventable stockouts during local demand spikes. Sales, inventory, product, store, promotion, weather, and event data exist in separate systems, making it hard for planners to understand what happened or predict what will happen next.

This project creates a lakehouse pipeline that helps answer:

- Which products and stores are most exposed to stockout risk?
- How much revenue was lost due to inventory gaps?
- Which external signals explain demand spikes?
- What should planners prioritize before the next replenishment cycle?

## Target Users

- Store operations leaders monitoring stockouts and lost sales.
- Inventory planners deciding replenishment priorities.
- Merchandising teams evaluating promotion effectiveness.
- Data science teams building demand and risk models.

## Discovery Context

The client discovery profile lives in [`docs/discovery/company-profile.md`](docs/discovery/company-profile.md). It defines NorthMart's operating model, stakeholder pains, source systems, business questions, and success metrics.

## Planned Architecture

```text
Synthetic and public data sources
        |
        v
Bronze: raw files and landing tables
        |
        v
Silver: cleaned, conformed, quality-checked entities
        |
        v
Gold: business marts, feature tables, prediction tables
        |
        v
Serving: SQL dashboards, Databricks App, ML outputs
```

## Learning Goals

- Build a medallion lakehouse with Databricks Free Edition constraints in mind.
- Use Unity Catalog volumes and tables responsibly.
- Model realistic retail data with skew, anomalies, and business impact.
- Add data quality checks where bad data would change decisions.
- Deploy workflows with Databricks bundles where practical.
- Train and evaluate lightweight ML models for forecasting or stockout risk.

## Repository Status

This repo is in the brainstorming and foundation phase. The next step is to choose the first thin vertical slice and implement it end to end.
