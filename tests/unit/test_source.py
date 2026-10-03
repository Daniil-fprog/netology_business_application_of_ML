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
