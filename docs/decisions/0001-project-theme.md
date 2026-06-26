# 0001: Project Theme

## Status

Accepted

## Context

The project should be challenging enough to practice ingestion, transformation, serving, and ML, while remaining realistic for Databricks Free Edition.

The theme also needs a clear business story so the project can be explained from a Solutions Architect perspective.

## Decision

Use a retail demand and inventory intelligence platform as the project theme.

## Rationale

Retail provides a strong learning surface:

- Multiple source types with clear relationships.
- Natural medallion architecture fit.
- Useful analytical marts and dashboards.
- Practical ML opportunities.
- Easy business framing around revenue, stockouts, promotions, and planning.

## Consequences

- The first implementation should prioritize a thin vertical slice over a broad data model.
- ML should start with interpretable baselines.
- Data generation should include non-uniform patterns, anomalies, and measurable business impact.
- The serving layer should initially favor SQL marts and AI/BI dashboards before custom apps.
