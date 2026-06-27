from __future__ import annotations


def store_key(sequence_number: int) -> str:
    """Return a stable NorthMart store key for sampled source stores."""
    return f"NM-STORE-{sequence_number:03d}"


def product_key(sequence_number: int) -> str:
    """Return a stable NorthMart product key for sampled source products."""
    return f"NM-SKU-{sequence_number:05d}"


NORTHMART_REGIONS = (
    "Rockies",
    "Wasatch",
    "Northern Plains",
    "High Desert",
)

NORTHMART_PRODUCT_CATEGORIES = (
    "Hiking",
    "Camping",
    "Fishing",
    "Winter Sports",
    "Apparel",
    "Footwear",
    "Travel",
    "Hydration",
)

REPLENISHMENT_CLASSES = (
    "fast",
    "standard",
    "slow",
    "seasonal",
)

NORTHMART_STATES = (
    ("Colorado", "CO", "Rockies", "mountain"),
    ("Utah", "UT", "Wasatch", "high_desert"),
    ("Montana", "MT", "Northern Plains", "northern"),
    ("Idaho", "ID", "Northern Plains", "mountain"),
    ("Wyoming", "WY", "High Desert", "high_desert"),
)

STORE_FORMATS = ("flagship", "standard", "outlet")

BRANDS = (
    "SummitTrail",
    "PineForge",
    "Riverline",
    "Snowcap",
    "Trailhead",
    "NorthRidge",
)

SEASONAL_PEAKS = ("spring", "summer", "fall", "winter", "year_round")

