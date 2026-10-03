import logging

from fastapi import APIRouter

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import (
    RecommendationRead,
    RecommendationRequest,
    RecommendationResponse,
)
from wine_recommendation.core.config import settings
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
    if payload.user_id is not None:
        repository.get_user(payload.user_id)
        preferred_pair = repository.preferred_pair(payload.user_id)
    service = RecommendationService(
        RankingWeights(
            rating=settings.rating_weight,
            price=settings.price_weight,
            popularity=settings.popularity_weight,
            preference_boost=settings.preference_boost,
        )
    )
    results = service.recommend(repository.candidates(), parsed, payload.limit, preferred_pair)
    repository.save_event(
        payload.user_id,
        payload.query,
        parsed.model_dump(exclude_none=True),
        [item.wine_id for item in results],
    )
    return RecommendationResponse(
        parsed_query=parsed,
        recommendations=[RecommendationRead.model_validate(item) for item in results],
    )
