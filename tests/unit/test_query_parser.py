import pytest

from wine_recommendation.query_parser.parser import QueryParseError, RuleBasedQueryParser


@pytest.fixture
def parser() -> RuleBasedQueryParser:
    return RuleBasedQueryParser()


def test_red_dry_with_max_price(parser: RuleBasedQueryParser) -> None:
    result = parser.parse("красное сухое до 1500")
    assert result.color == "red"
    assert result.sugar_type == "dry"
    assert result.min_price is None
    assert result.max_price == 1500


def test_white_with_price_range(parser: RuleBasedQueryParser) -> None:
    result = parser.parse("белое от 1000 до 2000")
    assert result.color == "white"
    assert result.min_price == 1000
    assert result.max_price == 2000


@pytest.mark.parametrize(
    ("query", "rating"),
    [("красное рейтинг от 4", 4), ("белое рейтинг выше 4,2", 4.2), ("от 4 звезд", 4)],
)
def test_rating(parser: RuleBasedQueryParser, query: str, rating: float) -> None:
    assert parser.parse(query).min_rating == rating


def test_unknown_color_is_not_guessed(parser: RuleBasedQueryParser) -> None:
    assert parser.parse("фиолетовое вино").color is None


def test_query_without_price(parser: RuleBasedQueryParser) -> None:
    result = parser.parse("белое сухое")
    assert result.min_price is None
    assert result.max_price is None


@pytest.mark.parametrize("query", ["", "   ", "красное до дорого"])
def test_invalid_query(parser: RuleBasedQueryParser, query: str) -> None:
    with pytest.raises(QueryParseError):
        parser.parse(query)


def test_invalid_price_range(parser: RuleBasedQueryParser) -> None:
    with pytest.raises(QueryParseError):
        parser.parse("от 2000 до 1000")
