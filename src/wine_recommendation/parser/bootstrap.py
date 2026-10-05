"""Load local demo data when the external parser is disabled."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from wine_recommendation.core.config import settings
from wine_recommendation.db.models import User, UserLike, Wine
from wine_recommendation.db.repositories import Repository
from wine_recommendation.db.session import SessionLocal
from wine_recommendation.parser.perekrestok import PerekrestokSource
from wine_recommendation.parser.service import ParserService

DATA_DIR = Path(__file__).parents[1] / "data"


def _read_mock_items(path: Path, key: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{path} must contain an array in the '{key}' field")
    return items


def _required_string(item: dict[str, Any], key: str, path: Path) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Every item in {path} must have a non-empty '{key}' field")
    return value.strip()


def load_mock_users_and_likes(session: Session) -> tuple[int, int]:
    """Upsert mock users and add their likes without creating duplicates."""
    users_path = DATA_DIR / "mock_users.json"
    likes_path = DATA_DIR / "mock_likes.json"
    user_items = _read_mock_items(users_path, "users")
    like_items = _read_mock_items(likes_path, "likes")

    external_ids = [_required_string(item, "external_id", users_path) for item in user_items]
    if len(external_ids) != len(set(external_ids)):
        raise ValueError(f"Duplicate external_id in {users_path}")

    users_by_external_id = {
        user.external_id: user
        for user in session.scalars(select(User).where(User.external_id.in_(external_ids)))
    }
    users_created = 0
    for item, external_id in zip(user_items, external_ids, strict=True):
        username_value = item.get("username")
        username = str(username_value).strip() if username_value is not None else None
        user = users_by_external_id.get(external_id)
        if user is None:
            user = User(external_id=external_id, username=username)
            session.add(user)
            users_by_external_id[external_id] = user
            users_created += 1
        else:
            user.username = username
    session.flush()

    wine_external_ids = {
        _required_string(item, "wine_external_id", likes_path) for item in like_items
    }
    wines_by_external_id = {
        wine.external_id: wine
        for wine in session.scalars(select(Wine).where(Wine.external_id.in_(wine_external_ids)))
    }
    missing_wines = wine_external_ids - wines_by_external_id.keys()
    if missing_wines:
        missing = ", ".join(sorted(missing_wines))
        raise ValueError(f"Unknown wine_external_id in {likes_path}: {missing}")

    existing_likes = set(session.execute(select(UserLike.user_id, UserLike.wine_id)).tuples())
    likes_created = 0
    for item in like_items:
        user_external_id = _required_string(item, "user_external_id", likes_path)
        wine_external_id = _required_string(item, "wine_external_id", likes_path)
        user = users_by_external_id.get(user_external_id)
        if user is None:
            raise ValueError(f"Unknown user_external_id in {likes_path}: {user_external_id}")
        wine = wines_by_external_id[wine_external_id]
        pair = (user.id, wine.id)
        if pair not in existing_likes:
            session.add(UserLike(user_id=user.id, wine_id=wine.id))
            existing_likes.add(pair)
            likes_created += 1

    session.commit()
    return users_created, likes_created


def load_mock_catalog() -> None:
    if settings.parser_enabled:
        return

    source_url = urlsplit(settings.mock_json_data)
    if source_url.scheme not in {"", "file"}:
        raise SystemExit("Automatic catalogue loading requires a local path in MOCK_JSON_DATA")

    source = PerekrestokSource(
        settings.mock_json_data,
        settings.parser_timeout,
        settings.parser_user_agent,
    )
    with SessionLocal() as session:
        updated = ParserService(source, Repository(session)).update()
        users_created, likes_created = load_mock_users_and_likes(session)
    print(
        f"Loaded {updated} wines; created {users_created} users and {likes_created} likes"
    )
