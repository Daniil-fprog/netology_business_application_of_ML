from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from wine_recommendation.api.dependencies import get_repository
from wine_recommendation.db.models import Base
from wine_recommendation.db.repositories import Repository
from wine_recommendation.main import app
from wine_recommendation.parser.schemas import ParsedWine


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_is_available() -> None:
    with TestClient(app) as client:
        page = client.get("/")
        script = client.get("/static/app.js")
    assert page.status_code == 200
    assert "recommendation-form" in page.text
    assert script.status_code == 200


def test_invalid_recommendation_request() -> None:
    with TestClient(app) as client:
        response = client.post("/recommendations", json={"query": ""})
    assert response.status_code == 422


def test_recommendation_flow() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = Repository(session)
        repository.upsert_wines(
            [
                ParsedWine(
                    external_id="wine-1",
                    name="Test Red",
                    price=Decimal("1200"),
                    color="red",
                    sugar_type="dry",
                    rating=4.5,
                    reviews_count=50,
                )
            ],
            "test",
        )
        app.dependency_overrides[get_repository] = lambda: repository
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/recommendations",
                    json={"query": "красное сухое до 1500", "limit": 5},
                )
        finally:
            app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["parsed_query"]["color"] == "red"
    assert body["recommendations"][0]["name"] == "Test Red"
