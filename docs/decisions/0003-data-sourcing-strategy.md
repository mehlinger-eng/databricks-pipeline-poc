# 0003: Data Sourcing Strategy

## Status

Accepted

## Context

NorthMart needs a realistic data story for stockouts, demand spikes, promotions, external signals, and inventory planning. The project also needs to stay manageable in Databricks Free Edition and remain easy to explain as a portfolio-quality learning project.

There are three viable approaches:

- Fully synthetic data gives maximum control over the business story but can feel artificial.
- Fully public data gives realism but may force the fictional client story to match someone else's schema, geography, license, and business context.
- A hybrid approach uses public data patterns where they add realism and synthetic data where the client story needs control.

## Decision

Use a hybrid data strategy.

NorthMart-specific master data, promotions, replenishment rules, and business events will be simulated. Demand, stockout, promotion, holiday, and external-signal behavior will be anchored by a small public retail dataset sample when practical.

The first public dataset candidate is **FreshRetailNet-50K** because it includes store-product time series, sales, stockout annotations, discount activity, holiday flags, and weather covariates. **Walmart M5** remains a useful fallback or secondary module for classic hierarchical forecasting, but it is not the first choice because it does not directly model inventory or stockouts.

## Rationale

Hybrid sourcing gives the project the strongest balance:

- Realistic behavioral patterns for demand and stockouts.
- A fictional client model that still supports clear stakeholder decisions.
- Compact data volumes that fit Databricks Free Edition.
- Enough source diversity to practice ingestion, conformance, quality checks, serving, and ML.
- Avoids spending the whole project on public dataset cleanup instead of architecture and pipeline design.

## Initial Source Plan

- Simulate NorthMart stores, products, categories, regions, replenishment classes, and planning attributes.
- Simulate client-specific promotions and local business events.
- Sample a public retail demand dataset into a small store-product-date window.
- Preserve raw public-source shape in bronze where useful.
- Conform public-source identifiers into NorthMart-style dimensions in silver.
- Build gold marts around stockout analysis, lost-sales proxy, promotion impact, and risk scoring.

## Incremental Runs

Incremental processing will be added after the first static vertical slice works.

The future pattern is a batch replay harness:

- Partition raw landing files by `run_date` or `batch_id`.
- Land only the next business-date slice during each run.
- Re-run bronze, silver, and gold transformations.
- Introduce late-arriving records, corrections, missing snapshots, and duplicate source exports as controlled test cases.

This keeps the first milestone simple while preserving a credible path to incremental pipeline behavior.

## Consequences

- The first implementation should not load the full public dataset.
- Data contracts need to distinguish raw source fields from NorthMart-conformed business fields.
- The project should document source provenance and licensing before publishing any sample data.
- The first ML use case should use features from the conformed gold layer, not raw public-source fields directly.
