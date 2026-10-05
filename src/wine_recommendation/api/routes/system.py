from fastapi import APIRouter, HTTPException, status

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import ParserUpdateResponse
from wine_recommendation.core.config import settings
from wine_recommendation.parser.perekrestok import PerekrestokSource
from wine_recommendation.parser.service import ParserService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/parser/update", response_model=ParserUpdateResponse)
def update_parser(repository: RepositoryDep) -> ParserUpdateResponse:
    if not settings.parser_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Парсер отключен. Проверьте условия источника и задайте PARSER_ENABLED=true.",
        )
    source = PerekrestokSource(
        endpoint=settings.mock_json_data,
        timeout=settings.parser_timeout,
        user_agent=settings.parser_user_agent,
    )
    updated = ParserService(source, repository).update()
    return ParserUpdateResponse(source=source.name, updated=updated)
