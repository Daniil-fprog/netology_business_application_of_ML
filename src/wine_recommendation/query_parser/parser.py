from __future__ import annotations

import re
from typing import Protocol

from wine_recommendation.query_parser.schemas import Color, SugarType, WineQuery


class QueryParser(Protocol):
    def parse(self, text: str) -> WineQuery: ...


class QueryParseError(ValueError):
    """User query cannot be parsed safely."""


class RuleBasedQueryParser:
    _colors = {
        "красное": Color.RED,
        "красный": Color.RED,
        "белое": Color.WHITE,
        "белый": Color.WHITE,
        "розовое": Color.ROSE,
        "розовый": Color.ROSE,
    }
    # Longer tokens must be checked first.
    _sugar_types = {
        "полусухое": SugarType.SEMI_DRY,
        "полусухой": SugarType.SEMI_DRY,
        "полусладкое": SugarType.SEMI_SWEET,
        "полусладкий": SugarType.SEMI_SWEET,
        "сухое": SugarType.DRY,
        "сухой": SugarType.DRY,
        "сладкое": SugarType.SWEET,
        "сладкий": SugarType.SWEET,
    }
    _number = r"(\d+(?:[.,]\d+)?)"
    _range = re.compile(rf"\bот\s+{_number}\s+(?:руб(?:лей|ля|ль)?\s+)?до\s+{_number}\b")
    _max_price = re.compile(rf"\bдо\s+{_number}(?:\s*(?:руб(?:лей|ля|ль)?|₽))?\b")
    _min_price = re.compile(rf"\bот\s+{_number}(?:\s*(?:руб(?:лей|ля|ль)?|₽))?\b")
    _rating = re.compile(
        rf"(?:\bрейтинг(?:ом)?\s*(?:от|выше)?\s*{_number}|\bот\s+{_number}\s*зв[её]зд)"
    )
    _malformed_price = re.compile(r"\b(?:до|от)\s+(?!\d)")

    def parse(self, text: str) -> WineQuery:
        normalized = " ".join(text.lower().replace("ё", "е").split())
        if not normalized:
            raise QueryParseError("Запрос не должен быть пустым")
        if self._malformed_price.search(normalized):
            raise QueryParseError("После 'до' или 'от' ожидается число")

        color = next((value for token, value in self._colors.items() if token in normalized), None)
        sugar = next(
            (value for token, value in self._sugar_types.items() if token in normalized), None
        )
        min_price: float | None = None
        max_price: float | None = None

        rating_match = self._rating.search(normalized)
        text_without_rating = self._rating.sub("", normalized)
        range_match = self._range.search(text_without_rating)
        if range_match:
            min_price = self._to_float(range_match.group(1))
            max_price = self._to_float(range_match.group(2))
        else:
            max_match = self._max_price.search(text_without_rating)
            min_match = self._min_price.search(text_without_rating)
            max_price = self._to_float(max_match.group(1)) if max_match else None
            min_price = self._to_float(min_match.group(1)) if min_match else None

        min_rating = None
        if rating_match:
            raw_rating = next(group for group in rating_match.groups() if group is not None)
            min_rating = self._to_float(raw_rating)
            if not 0 <= min_rating <= 5:
                raise QueryParseError("Рейтинг должен быть от 0 до 5")

        try:
            return WineQuery(
                color=color,
                sugar_type=sugar,
                min_price=min_price,
                max_price=max_price,
                min_rating=min_rating,
            )
        except ValueError as exc:
            raise QueryParseError(str(exc)) from exc

    @staticmethod
    def _to_float(value: str) -> float:
        return float(value.replace(",", "."))
