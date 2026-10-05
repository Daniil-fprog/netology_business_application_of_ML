from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from wine_recommendation.recommendation.schemas import WineCandidate

FeatureVector = dict[str, float]


@dataclass(frozen=True, slots=True)
class TrainingResult:
    trained_at: datetime
    wines_count: int
    users_count: int
    likes_count: int


class ContentBasedRecommender:
    """Content-based model trained on wine attributes and user likes."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._wine_vectors: dict[int, FeatureVector] = {}
        self._user_profiles: dict[int, FeatureVector] = {}
        self._result: TrainingResult | None = None

    @property
    def training_result(self) -> TrainingResult | None:
        with self._lock:
            return self._result

    def fit(
        self,
        wines: list[WineCandidate],
        likes_by_user: dict[int, set[int]],
    ) -> TrainingResult:
        price_scale = max((wine.price for wine in wines), default=1.0)
        wine_vectors = {wine.wine_id: self._wine_vector(wine, price_scale) for wine in wines}
        user_profiles: dict[int, FeatureVector] = {}
        likes_count = 0
        for user_id, liked_ids in likes_by_user.items():
            liked_vectors = [
                wine_vectors[wine_id] for wine_id in liked_ids if wine_id in wine_vectors
            ]
            if liked_vectors:
                user_profiles[user_id] = _normalize(_mean(liked_vectors))
                likes_count += len(liked_vectors)

        result = TrainingResult(
            trained_at=datetime.now(UTC),
            wines_count=len(wine_vectors),
            users_count=len(user_profiles),
            likes_count=likes_count,
        )
        with self._lock:
            self._wine_vectors = wine_vectors
            self._user_profiles = user_profiles
            self._result = result
        return result

    def scores(self, user_id: int, wine_ids: list[int]) -> dict[int, float] | None:
        with self._lock:
            profile = self._user_profiles.get(user_id)
            if profile is None:
                return None
            scores = {
                wine_id: round(_dot(profile, self._wine_vectors[wine_id]), 6)
                for wine_id in wine_ids
                if wine_id in self._wine_vectors
            }
            return scores or None

    @staticmethod
    def _wine_vector(wine: WineCandidate, price_scale: float) -> FeatureVector:
        vector: FeatureVector = {
            "numeric:price": wine.price / max(price_scale, 1.0),
            "numeric:rating": (wine.rating or 0.0) / 5.0,
        }
        _add_category(vector, "color", wine.color, 2.0)
        _add_category(vector, "sugar", wine.sugar_type, 2.0)
        _add_category(vector, "country", wine.country, 1.0)
        _add_category(vector, "brand", wine.brand, 0.75)
        if wine.grape:
            for grape in wine.grape.split(","):
                _add_category(vector, "grape", grape, 1.5)
        return _normalize(vector)


def _add_category(vector: FeatureVector, name: str, value: str | None, weight: float) -> None:
    if value and value.strip():
        vector[f"{name}:{value.strip().casefold()}"] = weight


def _mean(vectors: list[FeatureVector]) -> FeatureVector:
    result: FeatureVector = {}
    for vector in vectors:
        for feature, value in vector.items():
            result[feature] = result.get(feature, 0.0) + value / len(vectors)
    return result


def _normalize(vector: FeatureVector) -> FeatureVector:
    length = math.sqrt(sum(value * value for value in vector.values()))
    if length == 0:
        return vector
    return {feature: value / length for feature, value in vector.items()}


def _dot(left: FeatureVector, right: FeatureVector) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(feature, 0.0) for feature, value in left.items())
