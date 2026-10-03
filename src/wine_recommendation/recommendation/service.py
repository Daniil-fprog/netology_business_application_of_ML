from __future__ import annotations

from wine_recommendation.query_parser.schemas import WineQuery
from wine_recommendation.recommendation.ranking import RankingWeights, calculate_score
from wine_recommendation.recommendation.schemas import WineCandidate, WineRecommendation


class RecommendationService:
    def __init__(self, weights: RankingWeights | None = None) -> None:
        self.weights = weights or RankingWeights()

    def recommend(
        self,
        candidates: list[WineCandidate],
        query: WineQuery,
        limit: int = 5,
        preferred_pair: tuple[str, str] | None = None,
    ) -> list[WineRecommendation]:
        if limit < 1:
            raise ValueError("limit must be positive")
        filtered = [wine for wine in candidates if self._matches(wine, query)]
        max_reviews = max((wine.reviews_count for wine in filtered), default=0)
        ranked = [
            WineRecommendation(
                wine_id=wine.wine_id,
                name=wine.name,
                price=wine.price,
                rating=wine.rating,
                color=wine.color,
                sugar_type=wine.sugar_type,
                brand=wine.brand,
                country=wine.country,
                grape=wine.grape,
                image_url=wine.image_url,
                product_url=wine.product_url,
                score=calculate_score(wine, query, self.weights, max_reviews, preferred_pair),
            )
            for wine in filtered
        ]
        return sorted(ranked, key=lambda item: (-item.score, item.wine_id))[:limit]

    @staticmethod
    def _matches(wine: WineCandidate, query: WineQuery) -> bool:
        return not (
            (query.color is not None and wine.color != query.color)
            or (query.sugar_type is not None and wine.sugar_type != query.sugar_type)
            or (query.min_price is not None and wine.price < query.min_price)
            or (query.max_price is not None and wine.price > query.max_price)
            or (query.min_rating is not None and (wine.rating or 0) < query.min_rating)
        )
