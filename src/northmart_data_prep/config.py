from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path


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

    @property
    def output_path(self) -> Path:
        return Path(self.output_root)


@dataclass(frozen=True)
class ReplayConfig:
    """Plan for replaying the static slice as time-ordered incremental batches.

    The full 90-day slice is split into a seed plus two increments. A final
    restatement batch arrives out of order to exercise late-arriving and
    corrected records:

    - Late-arriving: one store's earliest days are withheld from the seed and
      delivered later, so a previously processed date gains new rows.
    - Corrected: a deterministic set of already-published keys is re-emitted
      with materially changed measures and a higher ``batch_seq`` so silver's
      latest-wins logic restates them.
    """

    seed_days: int = 60
    increment_days: tuple[int, ...] = (15, 15)
    output_root: str = "data/generated/northmart_replay"

    # Late-arriving: source store id whose earliest `late_store_days` are held
    # back from the seed and delivered in the restatement batch.
    late_store_id: int = 10007
    late_store_days: int = 15

    # Corrected: re-emit these source products for `correction_store_id` on the
    # given day offsets (relative to the slice start) with boosted demand and
    # forced stockouts to make the restatement visible in gold.
    correction_store_id: int = 10000
    correction_product_ids: tuple[int, ...] = (50000, 50001, 50002, 50003, 50004)
    correction_day_offsets: tuple[int, ...] = (5, 6, 7)

    batches: tuple[tuple[str, int], ...] = field(
        default_factory=lambda: (
            ("replay-001-seed", 1),
            ("replay-002-inc", 2),
            ("replay-003-inc", 3),
            ("replay-004-restatement", 4),
        )
    )

    @property
    def output_path(self) -> Path:
        return Path(self.output_root)

