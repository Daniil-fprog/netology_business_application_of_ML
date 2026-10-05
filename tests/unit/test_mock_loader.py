from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from wine_recommendation.db.models import Base, User, UserLike
from wine_recommendation.db.repositories import Repository
from wine_recommendation.parser import bootstrap
from wine_recommendation.parser.mock_json import MockJsonSource


def test_loader_is_skipped_when_parser_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "settings",
        SimpleNamespace(parser_enabled=True),
    )

    def unexpected_source(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("mock loader must be skipped")

    monkeypatch.setattr(bootstrap, "MockJsonSource", unexpected_source)

    bootstrap.load_mock_catalog()


def test_loader_rejects_remote_source_when_parser_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bootstrap,
        "settings",
        SimpleNamespace(
            parser_enabled=False,
            mock_json_data="https://example.com/catalogue.json",
        ),
    )

    with pytest.raises(SystemExit, match="requires a local path"):
        bootstrap.load_mock_catalog()


def test_mock_users_and_likes_are_loaded_idempotently() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    wines_path = bootstrap.DATA_DIR / "mock_wines.json"
    wines = MockJsonSource(str(wines_path)).fetch()

    with Session(engine) as session:
        Repository(session).upsert_wines(wines, "test")

        assert bootstrap.load_mock_users_and_likes(session) == (20, 120)
        assert bootstrap.load_mock_users_and_likes(session) == (0, 0)
        assert session.scalar(select(func.count()).select_from(User)) == 20
        assert session.scalar(select(func.count()).select_from(UserLike)) == 120
