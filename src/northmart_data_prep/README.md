# NorthMart Data Prep

Utilities for planning and preparing the first NorthMart thin-slice dataset.

The current scaffold is intentionally lightweight:

- Defines the default sample size.
- Defines deterministic NorthMart store and product keys.
- Prints the planned bronze, silver, and gold outputs.
- Does not download public data.
- Does not write generated datasets into the repository.

Run from the repository root:

```bash
PYTHONPATH=src python3 -m northmart_data_prep.sample_plan
```

Override the slice size within the Phase 1 guardrails:

```bash
PYTHONPATH=src python3 -m northmart_data_prep.sample_plan --stores 8 --products 80 --days 90
```

