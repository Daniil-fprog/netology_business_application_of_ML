from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from wine_recommendation.parser.base import SourceError
from wine_recommendation.parser.schemas import ParsedWine

logger = logging.getLogger(__name__)


class PerekrestokSource:
    """Adapter for an approved JSON catalogue endpoint.

    The endpoint is deliberately configured externally: storefront endpoints and
    usage terms change. It may return a list or an object with `items`/`products`.
    """

    name = "perekrestok"

    def __init__(self, endpoint: str, timeout: float, user_agent: str) -> None:
        if not endpoint:
            raise ValueError("MOCK_JSON_DATA is not configured")
        self.endpoint = endpoint
        self.timeout = timeout
        self.user_agent = user_agent

    def fetch(self) -> list[ParsedWine]:
        logger.info("Starting source fetch", extra={"source": self.name})
        try:
            payload = self._load_payload()
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            logger.exception("Source fetch failed", extra={"source": self.name})
            raise SourceError("Не удалось получить данные источника") from exc

        raw_items = self._items(payload)
        parsed: list[ParsedWine] = []
        for raw in raw_items:
            try:
                parsed.append(self.parse_item(raw))
            except (KeyError, TypeError, ValueError, InvalidOperation):
                logger.warning("Skipping invalid source item", exc_info=True)
        logger.info("Source fetch completed: %d items", len(parsed))
        return parsed

    def _load_payload(self) -> Any:
        parsed_url = urlsplit(self.endpoint)
        if parsed_url.scheme in {"http", "https"}:
            request = Request(
                self.endpoint,
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            )
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                return json.load(response)

        if parsed_url.scheme == "file":
            path = Path(unquote(parsed_url.path))
        elif not parsed_url.scheme:
            path = Path(self.endpoint)
        else:
            raise SourceError("Источник должен быть HTTP(S)-адресом или локальным JSON-файлом")

        with path.open(encoding="utf-8") as source_file:
            return json.load(source_file)

    @staticmethod
    def _items(payload: Any) -> list[Mapping[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, Mapping):
            for key in ("items", "products"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, Mapping)]
        raise SourceError("Неизвестный формат ответа источника")

    @staticmethod
    def parse_item(raw: Mapping[str, Any]) -> ParsedWine:
        external_id = str(raw.get("id") or raw.get("external_id") or "").strip()
        name = str(raw.get("name") or raw.get("title") or "").strip()
        if not external_id or not name:
            raise ValueError("id and name are required")
        price = Decimal(str(raw["price"]))
        if price < 0:
            raise ValueError("price must be non-negative")
        return ParsedWine(
            external_id=external_id,
            name=name,
            price=price,
            brand=_optional_string(raw.get("brand")),
            country=_optional_string(raw.get("country")),
            region=_optional_string(raw.get("region")),
            color=_normalize_color(raw.get("color")),
            sugar_type=_normalize_sugar(raw.get("sugar_type") or raw.get("sugar")),
            grape=_optional_string(raw.get("grape")),
            volume=_optional_float(raw.get("volume")),
            description=_optional_string(raw.get("description")),
            image_url=_optional_string(raw.get("image_url") or raw.get("image")),
            product_url=_optional_string(raw.get("product_url") or raw.get("url")),
            old_price=_optional_decimal(raw.get("old_price")),
            is_available=bool(raw.get("is_available", True)),
            rating=_optional_float(raw.get("rating")),
            reviews_count=int(raw.get("reviews_count") or 0),
        )


def _optional_string(value: Any) -> str | None:
    return str(value).strip() if value not in (None, "") else None


def _optional_float(value: Any) -> float | None:
    return float(value) if value not in (None, "") else None


def _optional_decimal(value: Any) -> Decimal | None:
    return Decimal(str(value)) if value not in (None, "") else None


def _normalize_color(value: Any) -> str | None:
    mapping = {"красное": "red", "белое": "white", "розовое": "rose"}
    normalized = _optional_string(value)
    return mapping.get(normalized.lower(), normalized.lower()) if normalized else None


def _normalize_sugar(value: Any) -> str | None:
    mapping = {
        "сухое": "dry",
        "полусухое": "semi_dry",
        "полусладкое": "semi_sweet",
        "сладкое": "sweet",
    }
    normalized = _optional_string(value)
    return mapping.get(normalized.lower(), normalized.lower()) if normalized else None
