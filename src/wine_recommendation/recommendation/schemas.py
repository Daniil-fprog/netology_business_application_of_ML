from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WineCandidate:
    wine_id: int
    name: str
    color: str | None
    sugar_type: str | None
    price: float
    rating: float | None = None
    reviews_count: int = 0
    brand: str | None = None
    country: str | None = None
    grape: str | None = None
    image_url: str | None = None
    product_url: str | None = None


@dataclass(frozen=True, slots=True)
class WineRecommendation:
    wine_id: int
    name: str
    price: float
    rating: float | None
    color: str | None
    sugar_type: str | None
    brand: str | None
    country: str | None
    grape: str | None
    image_url: str | None
    product_url: str | None
    score: float
