from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date


@dataclass(frozen=True)
class ThinSliceConfig:
    """Configuration for the first static NorthMart data slice."""

    source_dataset: str = "Dingdong-Inc/FreshRetailNet-50K"
    source_split: str = "train"
    store_count: int = 8
    product_count: int = 80
    start_date: date = date(2024, 3, 1)
    day_count: int = 90
    batch_id: str = "static-001"
    output_root: str = "data/generated/northmart_thin_slice"

    def validate(self) -> None:
        if not 5 <= self.store_count <= 10:
            raise ValueError("store_count should stay between 5 and 10 for the first slice")
        if not 50 <= self.product_count <= 100:
            raise ValueError("product_count should stay between 50 and 100 for the first slice")
        if self.day_count != 90:
            raise ValueError("day_count should remain 90 until the first slice is proven")
        if not self.batch_id:
            raise ValueError("batch_id is required")

    def to_dict(self) -> dict[str, object]:
        values = asdict(self)
        values["start_date"] = self.start_date.isoformat()
        return values

