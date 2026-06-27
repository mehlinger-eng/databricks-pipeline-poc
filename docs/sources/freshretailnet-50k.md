# FreshRetailNet-50K Source Validation

## Source

- Dataset: `Dingdong-Inc/FreshRetailNet-50K`
- Host: Hugging Face Datasets
- Developer: Dingdong-Inc
- Version: 1.0
- Release date: 2025-05-08
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Intended use: latent demand recovery and demand forecasting research

## Why It Fits NorthMart

FreshRetailNet-50K is a strong behavioral anchor for the NorthMart thin slice because it includes the signals NorthMart cares about:

- Store-product time series.
- Sales or demand observations.
- Explicit stockout annotations.
- Discount and activity signals.
- Holiday flags.
- Weather covariates such as precipitation, temperature, humidity, and wind.

The raw dataset is not NorthMart data. We use it as a public behavioral pattern source and map a compact sample into NorthMart's fictional operating model.

## Source Schema

| Field | Type | Notes |
| --- | --- | --- |
| `city_id` | int64 | Encoded city identifier. |
| `store_id` | int64 | Encoded store identifier. |
| `management_group_id` | int64 | Encoded product management group. |
| `first_category_id` | int64 | Encoded top-level category. |
| `second_category_id` | int64 | Encoded second-level category. |
| `third_category_id` | int64 | Encoded third-level category. |
| `product_id` | int64 | Encoded product identifier. |
| `dt` | string | Business date. |
| `sale_amount` | float64 | Daily sales amount after global normalization. |
| `hours_sale` | array<float64> | Hourly sales profile. |
| `stock_hour6_22_cnt` | int32 | Out-of-stock hours between 06:00 and 22:00. |
| `hours_stock_status` | array<int32> | Hourly stockout status. |
| `discount` | float64 | Discount rate; `1.0` means no discount. |
| `holiday_flag` | int32 | Holiday indicator. |
| `activity_flag` | int32 | Promotion/activity indicator. |
| `precpt` | float64 | Total precipitation. |
| `avg_temperature` | float64 | Average temperature. |
| `avg_humidity` | float64 | Average humidity. |
| `avg_wind_level` | float64 | Average wind force. |

## Access Pattern

The dataset can be loaded with Hugging Face Datasets:

```python
from datasets import load_dataset

dataset = load_dataset("Dingdong-Inc/FreshRetailNet-50K")
```

The full dataset has about 4.85 million rows and a total file size around 115 MB. For this project, do not ingest the full dataset in the first iteration.

## Thin Slice Sample

Initial sample target:

- 5 to 10 stores.
- 50 to 100 products.
- 90 business days.
- Daily grain for the first gold mart.

This keeps the first slice small while preserving meaningful stockout and demand patterns.

## License and Attribution Notes

FreshRetailNet-50K is CC BY 4.0. Any public use of derived data, examples, or documentation should attribute Dingdong-Inc and cite the associated paper.

Do not commit downloaded source data or generated sample extracts to this repository unless the sample is intentionally tiny, license-compatible, and clearly attributed.
