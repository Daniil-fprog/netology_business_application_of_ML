from fastapi import APIRouter, Query, Response, status

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import LikeCreate, LikeRead, UserCreate, UserRead, WineRead

router = APIRouter()


@router.get("/wines", response_model=list[WineRead])
def list_wines(
    repository: RepositoryDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[WineRead]:
    return [WineRead.model_validate(item) for item in repository.list_wines(offset, limit)]


@router.get("/wines/{wine_id}", response_model=WineRead)
def get_wine(wine_id: int, repository: RepositoryDep) -> WineRead:
    return WineRead.model_validate(repository.get_wine(wine_id))


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, repository: RepositoryDep) -> UserRead:
    return UserRead.model_validate(repository.create_user(payload.external_id, payload.username))


@router.post("/users/{user_id}/likes", response_model=LikeRead, status_code=status.HTTP_201_CREATED)
def add_like(user_id: int, payload: LikeCreate, repository: RepositoryDep) -> LikeRead:
    return LikeRead.model_validate(repository.add_like(user_id, payload.wine_id))


@router.delete("/users/{user_id}/likes/{wine_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_like(user_id: int, wine_id: int, repository: RepositoryDep) -> Response:
    repository.remove_like(user_id, wine_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
