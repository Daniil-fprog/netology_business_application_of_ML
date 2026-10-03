import json
from decimal import Decimal
from pathlib import Path

import pytest

from wine_recommendation.parser.base import SourceError
from wine_recommendation.parser.perekrestok import PerekrestokSource


def test_parse_saved_fixture() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "perekrestok.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    item = PerekrestokSource.parse_item(payload["items"][0])
    assert item.external_id == "sku-1"
    assert item.color == "red"
    assert item.sugar_type == "dry"
    assert item.price == Decimal("999.9")


def test_missing_optional_fields_are_allowed() -> None:
    item = PerekrestokSource.parse_item({"id": "1", "name": "Wine", "price": 100})
    assert item.country is None
    assert item.rating is None


def test_unknown_payload_format() -> None:
    with pytest.raises(SourceError):
        PerekrestokSource._items({"unexpected": []})


def test_fetch_from_local_json_file() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "perekrestok.json"
    source = PerekrestokSource(str(path), timeout=15, user_agent="test")

    items = source.fetch()

    assert len(items) == 1
    assert items[0].external_id == "sku-1"


def test_mock_catalog_contains_recommendation_variants() -> None:
    path = Path(__file__).parents[2] / "src" / "wine_recommendation" / "data" / "mock_wines.json"
    source = PerekrestokSource(str(path), timeout=15, user_agent="test")

    items = source.fetch()

    assert len(items) == 16
    assert {item.color for item in items} == {"red", "white", "rose"}
    assert {item.sugar_type for item in items} == {
        "dry",
        "semi_dry",
        "semi_sweet",
    }
