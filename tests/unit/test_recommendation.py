from wine_recommendation.query_parser.schemas import WineQuery
from wine_recommendation.recommendation.schemas import WineCandidate
from wine_recommendation.recommendation.service import RecommendationService


def wine(
    wine_id: int,
    *,
    color: str = "red",
    sugar: str = "dry",
    price: float = 1000,
    rating: float = 4,
    reviews: int = 10,
) -> WineCandidate:
    return WineCandidate(
        wine_id=wine_id,
        name=f"Wine {wine_id}",
        color=color,
        sugar_type=sugar,
        price=price,
        rating=rating,
        reviews_count=reviews,
    )


def test_filters_by_price_color_sugar_and_rating() -> None:
    candidates = [
        wine(1),
        wine(2, color="white"),
        wine(3, sugar="sweet"),
        wine(4, price=2000),
        wine(5, rating=3),
    ]
    query = WineQuery(color="red", sugar_type="dry", max_price=1500, min_rating=3.5)
    assert [item.wine_id for item in RecommendationService().recommend(candidates, query)] == [1]


def test_results_are_sorted_by_score() -> None:
    candidates = [wine(1, rating=3, reviews=1), wine(2, rating=5, reviews=100)]
    result = RecommendationService().recommend(candidates, WineQuery())
    assert [item.wine_id for item in result] == [2, 1]
    assert result[0].score > result[1].score


def test_top_n() -> None:
    result = RecommendationService().recommend(
        [wine(i, rating=float(i)) for i in range(1, 6)], WineQuery(), limit=2
    )
    assert len(result) == 2
    assert [item.wine_id for item in result] == [5, 4]


def test_no_matches() -> None:
    result = RecommendationService().recommend([wine(1, color="red")], WineQuery(color="white"))
    assert result == []


def test_like_preference_adds_small_boost() -> None:
    candidates = [wine(1), wine(2, color="white")]
    result = RecommendationService().recommend(
        candidates, WineQuery(), preferred_pair=("red", "dry")
    )
    assert result[0].wine_id == 1
