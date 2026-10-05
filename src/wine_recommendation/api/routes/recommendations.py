import logging

from fastapi import APIRouter

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import (
    RecommendationRead,
    RecommendationRequest,
    RecommendationResponse,
)
from wine_recommendation.core.config import settings
from wine_recommendation.ml import recommender
from wine_recommendation.query_parser.parser import RuleBasedQueryParser
from wine_recommendation.recommendation.ranking import RankingWeights
from wine_recommendation.recommendation.service import RecommendationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
def recommendations(
    payload: RecommendationRequest, repository: RepositoryDep
) -> RecommendationResponse:
    logger.info("Recommendation requested", extra={"user_id": payload.user_id})
    parsed = RuleBasedQueryParser().parse(payload.query)
    preferred_pair = None
    liked_wine_ids: set[int] = set()
    if payload.user_id is not None:
        repository.get_user(payload.user_id)
        preferred_pair = repository.preferred_pair(payload.user_id)
        liked_wine_ids = repository.liked_wine_ids(payload.user_id)
    service = RecommendationService(
        RankingWeights(
            rating=settings.rating_weight,
            price=settings.price_weight,
            popularity=settings.popularity_weight,
            preference_boost=settings.preference_boost,
        )
    )
    candidates = repository.candidates()
    personalized_scores = None
    if payload.user_id is not None and liked_wine_ids:
        personalized_scores = recommender.scores(
            payload.user_id, [wine.wine_id for wine in candidates]
        )
    ml_active = personalized_scores is not None
    results = service.recommend(
        candidates,
        parsed,
        payload.limit,
        preferred_pair,
        personalized_scores=personalized_scores,
        excluded_wine_ids=liked_wine_ids if ml_active else None,
        personalization_weight=settings.ml_personalization_weight,
    )
    repository.save_event(
        payload.user_id,
        payload.query,
        parsed.model_dump(exclude_none=True),
        [item.wine_id for item in results],
    )
    return RecommendationResponse(
        parsed_query=parsed,
        recommendation_mode="ml" if ml_active else "standard",
        recommendations=[RecommendationRead.model_validate(item) for item in results],
    )
