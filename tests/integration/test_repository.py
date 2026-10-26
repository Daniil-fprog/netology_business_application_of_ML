from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from wine_recommendation.db.models import Base, Wine, WineOffer
from wine_recommendation.db.repositories import Repository
from wine_recommendation.parser.schemas import ParsedWine
from wine_recommendation.recommendation.filters import WineFilters


def test_upsert_updates_existing_offer_and_marks_missing_unavailable() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = Repository(session)
        repository.upsert_wines(
            [
                ParsedWine(external_id="1", name="A", price=Decimal("100")),
                ParsedWine(external_id="2", name="B", price=Decimal("200")),
            ],
            "test",
        )
        repository.upsert_wines(
            [ParsedWine(external_id="1", name="A new", price=Decimal("150"))], "test"
        )

        wines = list(session.scalars(select(Wine).order_by(Wine.external_id)))
        offers = list(session.scalars(select(WineOffer).order_by(WineOffer.wine_id)))
        assert [wine.name for wine in wines] == ["A new", "B"]
        assert offers[0].price == Decimal("150.00")
        assert offers[0].is_available is True
        assert offers[1].is_available is False


def test_candidates_applies_structured_filters_in_database() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        repository = Repository(session)
        repository.upsert_wines(
            [
                ParsedWine(
                    external_id="red-dry",
                    name="Red Dry",
                    price=Decimal("1200"),
                    color="red",
                    sugar_type="dry",
                    rating=4.5,
                ),
                ParsedWine(
                    external_id="white-dry",
                    name="White Dry",
                    price=Decimal("1200"),
                    color="white",
                    sugar_type="dry",
                    rating=4.5,
                ),
                ParsedWine(
                    external_id="red-expensive",
                    name="Red Expensive",
                    price=Decimal("2500"),
                    color="red",
                    sugar_type="dry",
                    rating=4.5,
                ),
            ],
            "test",
        )

        candidates = repository.candidates(
            WineFilters(color="red", sugar_type="dry", max_price=1500, min_rating=4)
        )

    assert [candidate.name for candidate in candidates] == ["Red Dry"]
