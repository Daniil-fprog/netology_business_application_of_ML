from fastapi import APIRouter, HTTPException, status

from wine_recommendation.api.dependencies import RepositoryDep
from wine_recommendation.api.schemas import ParserUpdateResponse
from wine_recommendation.core.config import settings
from wine_recommendation.parser.mock_json import MockJsonSource
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
    source = MockJsonSource(settings.mock_json_data)
    updated = ParserService(source, repository).update()
    return ParserUpdateResponse(source=source.name, updated=updated)
