from wine_recommendation.ml.recommender import ContentBasedRecommender
from wine_recommendation.query_parser.schemas import WineQuery
from wine_recommendation.recommendation.schemas import WineCandidate
from wine_recommendation.recommendation.service import RecommendationService


def wine(
    wine_id: int,
    *,
    color: str,
    sugar: str,
    country: str,
    grape: str,
) -> WineCandidate:
    return WineCandidate(
        wine_id=wine_id,
        name=f"Wine {wine_id}",
        color=color,
        sugar_type=sugar,
        country=country,
        grape=grape,
        price=1000,
        rating=4.5,
        reviews_count=10,
    )


def test_model_learns_user_profile_from_likes() -> None:
    wines = [
        wine(1, color="red", sugar="dry", country="Italy", grape="Sangiovese"),
        wine(2, color="red", sugar="dry", country="Italy", grape="Sangiovese"),
        wine(3, color="white", sugar="sweet", country="Germany", grape="Riesling"),
    ]
    model = ContentBasedRecommender()

    result = model.fit(wines, {42: {1}})
    scores = model.scores(42, [2, 3])

    assert result.wines_count == 3
    assert result.users_count == 1
    assert result.likes_count == 1
    assert scores is not None
    assert scores[2] > scores[3]
    assert model.scores(100, [2, 3]) is None


def test_personalized_ranking_excludes_liked_wines() -> None:
    wines = [
        wine(1, color="red", sugar="dry", country="Italy", grape="Sangiovese"),
        wine(2, color="red", sugar="dry", country="Italy", grape="Sangiovese"),
        wine(3, color="white", sugar="sweet", country="Germany", grape="Riesling"),
    ]
    model = ContentBasedRecommender()
    model.fit(wines, {42: {1}})
    scores = model.scores(42, [wine.wine_id for wine in wines])

    results = RecommendationService().recommend(
        wines,
        WineQuery(),
        personalized_scores=scores,
        excluded_wine_ids={1},
    )

    assert [item.wine_id for item in results] == [2, 3]
