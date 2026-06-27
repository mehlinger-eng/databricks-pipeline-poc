# Roadmap

## Phase 0: Foundation

- Define the business story and project architecture.
- Create Cursor project guidance.
- Initialize the repository and GitHub project.

## Phase 1: Thin Vertical Slice

- Generate and ingest a small coherent hybrid retail dataset.
- Land raw files in a Unity Catalog volume.
- Build bronze ingestion tables.
- Build one silver fact table and one or two dimensions.
- Build one gold mart for stockout and lost-sales analysis.
- Query the result from Databricks SQL.

## Phase 2: Full Medallion Pipeline

- Expand the source set to sales, inventory, products, stores, promotions, calendar, and external signals.
- Add data quality checks.
- Add replay-based incremental ingestion patterns.
- Add late-arriving and corrected record handling.
- Package pipeline assets for deployment.

## Phase 3: Serving

- Create SQL marts for operations, inventory planning, and merchandising.
- Build an AI/BI dashboard.
- Evaluate whether a Databricks App adds enough value to justify custom code.

## Phase 4: ML

- Create feature tables for demand and stockout modeling.
- Train a baseline demand forecast or stockout-risk model.
- Log experiments and metrics with MLflow.
- Write predictions back to a serving table.

## Phase 5: Portfolio Polish

- Add architecture diagrams.
- Add sample dashboard screenshots.
- Document tradeoffs and Free Edition constraints.
- Add a final walkthrough showing how a planner uses the platform.
