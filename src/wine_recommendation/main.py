import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from wine_recommendation.api.routes import recommendations, system, wines
from wine_recommendation.core.config import settings
from wine_recommendation.core.logging import configure_logging
from wine_recommendation.db.repositories import Repository
from wine_recommendation.db.repositories.repository import ConflictError, NotFoundError
from wine_recommendation.db.session import SessionLocal
from wine_recommendation.ml import train_recommender
from wine_recommendation.parser.base import SourceError
from wine_recommendation.query_parser.parser import QueryParseError

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Application started")
    if settings.ml_train_on_startup:
        with SessionLocal() as session:
            result = train_recommender(Repository(session))
        logger.info(
            "ML model trained: %d wines, %d users, %d likes",
            result.wines_count,
            result.users_count,
            result.likes_count,
        )
    yield
    logger.info("Application stopped")


app = FastAPI(title="Wine Recommendation Service", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(system.router, tags=["system"])
app.include_router(wines.router, tags=["catalogue"])
app.include_router(recommendations.router, tags=["recommendations"])


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.exception_handler(NotFoundError)
async def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(QueryParseError)
async def query_error(_: Request, exc: QueryParseError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(SourceError)
async def source_error(_: Request, exc: SourceError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})
