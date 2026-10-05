from wine_recommendation.db.repositories import Repository
from wine_recommendation.ml.recommender import ContentBasedRecommender, TrainingResult

recommender = ContentBasedRecommender()


def train_recommender(repository: Repository) -> TrainingResult:
    return recommender.fit(repository.candidates(), repository.likes_by_user())
