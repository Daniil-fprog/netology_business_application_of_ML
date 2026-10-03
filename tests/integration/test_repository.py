from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from wine_recommendation.db.models import Base, Wine, WineOffer
from wine_recommendation.db.repositories import Repository
from wine_recommendation.parser.schemas import ParsedWine


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
