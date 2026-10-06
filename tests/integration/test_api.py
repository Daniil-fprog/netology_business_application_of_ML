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
    assert "profile-switcher" in page.text
    assert script.status_code == 200


def test_list_users() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = Repository(session)
        first_user = repository.create_user("first-user", "Алексей")
        second_user = repository.create_user("second-user", "Мария")
        app.dependency_overrides[get_repository] = lambda: repository
        try:
            with TestClient(app) as client:
                response = client.get("/users")
        finally:
            app.dependency_overrides.clear()
        expected = [
            {
                "id": first_user.id,
                "external_id": "first-user",
                "username": "Алексей",
                "created_at": first_user.created_at.isoformat(),
            },
            {
                "id": second_user.id,
                "external_id": "second-user",
                "username": "Мария",
                "created_at": second_user.created_at.isoformat(),
            },
        ]

    assert response.status_code == 200
    assert response.json() == expected


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
    assert body["recommendation_mode"] == "standard"


def test_ml_retrain_and_personalized_recommendations() -> None:
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
                    external_id="liked-red",
                    name="Liked Red",
                    price=Decimal("1000"),
                    color="red",
                    sugar_type="dry",
                    country="Italy",
                    grape="Sangiovese",
                    rating=4.5,
                    reviews_count=10,
                ),
                ParsedWine(
                    external_id="similar-red",
                    name="Similar Red",
                    price=Decimal("1000"),
                    color="red",
                    sugar_type="dry",
                    country="Italy",
                    grape="Sangiovese",
                    rating=4.5,
                    reviews_count=10,
                ),
                ParsedWine(
                    external_id="different-white",
                    name="Different White",
                    price=Decimal("1000"),
                    color="white",
                    sugar_type="sweet",
                    country="Germany",
                    grape="Riesling",
                    rating=4.5,
                    reviews_count=10,
                ),
            ],
            "test",
        )
        user = repository.create_user("ml-user", "ML User")
        user_without_likes = repository.create_user("cold-user", "Cold User")
        liked_wine = repository.list_wines(limit=1)[0]
        repository.add_like(user.id, liked_wine.id)
        app.dependency_overrides[get_repository] = lambda: repository
        try:
            with TestClient(app) as client:
                training_response = client.post("/ml/retrain")
                personalized_response = client.post(
                    "/recommendations",
                    json={"user_id": user.id, "query": "вино до 2000", "limit": 3},
                )
                fallback_response = client.post(
                    "/recommendations",
                    json={"user_id": user_without_likes.id, "query": "вино до 2000"},
                )
        finally:
            app.dependency_overrides.clear()

    assert training_response.status_code == 200
    assert training_response.json()["users_count"] == 1
    assert training_response.json()["likes_count"] == 1
    assert personalized_response.status_code == 200
    personalized_body = personalized_response.json()
    assert personalized_body["recommendation_mode"] == "ml"
    assert personalized_body["recommendations"][0]["name"] == "Similar Red"
    assert "Liked Red" not in [item["name"] for item in personalized_body["recommendations"]]
    assert fallback_response.status_code == 200
    assert fallback_response.json()["recommendation_mode"] == "standard"
