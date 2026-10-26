from __future__ import annotations

import math
from dataclasses import dataclass

from wine_recommendation.recommendation.filters import WineFilters
from wine_recommendation.recommendation.schemas import WineCandidate


@dataclass(frozen=True, slots=True)
class RankingWeights:
    rating: float = 0.55
    price: float = 0.25
    popularity: float = 0.20
    preference_boost: float = 0.05

    def __post_init__(self) -> None:
        if min(self.rating, self.price, self.popularity, self.preference_boost) < 0:
            raise ValueError("Ranking weights cannot be negative")


def calculate_score(
    wine: WineCandidate,
    filters: WineFilters,
    weights: RankingWeights,
    max_reviews: int,
    preferred_pair: tuple[str, str] | None = None,
) -> float:
    rating_score = min(max((wine.rating or 0) / 5, 0), 1)
    popularity_score = math.log1p(wine.reviews_count) / math.log1p(max(max_reviews, 1))
    price_score = _price_score(wine.price, filters)
    preference = (
        weights.preference_boost if preferred_pair == (wine.color, wine.sugar_type) else 0.0
    )
    return round(
        weights.rating * rating_score
        + weights.price * price_score
        + weights.popularity * popularity_score
        + preference,
        6,
    )


def _price_score(price: float, filters: WineFilters) -> float:
    if filters.min_price is not None and filters.max_price is not None:
        center = (filters.min_price + filters.max_price) / 2
        half_range = max((filters.max_price - filters.min_price) / 2, 1)
        return max(0.0, 1 - abs(price - center) / half_range)
    if filters.max_price is not None:
        return max(0.0, 1 - price / max(filters.max_price, 1))
    if filters.min_price is not None:
        return min(1.0, filters.min_price / max(price, 1))
    return 1.0
