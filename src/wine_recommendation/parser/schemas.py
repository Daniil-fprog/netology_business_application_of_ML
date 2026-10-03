from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ParsedWine:
    external_id: str
    name: str
    price: Decimal
    brand: str | None = None
    country: str | None = None
    region: str | None = None
    color: str | None = None
    sugar_type: str | None = None
    grape: str | None = None
    volume: float | None = None
    description: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    old_price: Decimal | None = None
    is_available: bool = True
    rating: float | None = None
    reviews_count: int = 0

    def wine_values(self) -> dict[str, object]:
        return {
            "name": self.name,
            "brand": self.brand,
            "country": self.country,
            "region": self.region,
            "color": self.color,
            "sugar_type": self.sugar_type,
            "grape": self.grape,
            "volume": self.volume,
            "description": self.description,
            "image_url": self.image_url,
            "product_url": self.product_url,
        }

    def offer_values(self) -> dict[str, object]:
        return {
            "price": self.price,
            "old_price": self.old_price,
            "is_available": self.is_available,
            "external_rating": self.rating,
            "reviews_count": self.reviews_count,
            "product_url": self.product_url,
        }
