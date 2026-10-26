from fastapi import APIRouter

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import MLTrainingResponse
from wine_recommendation.ml import train_recommender

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/ml/retrain", response_model=MLTrainingResponse)
def retrain_ml_model(repository: RepositoryDep) -> MLTrainingResponse:
    result = train_recommender(repository)
    return MLTrainingResponse(
        trained_at=result.trained_at,
        wines_count=result.wines_count,
        users_count=result.users_count,
        likes_count=result.likes_count,
    )
