import logging

from wine_recommendation.db.repositories import Repository
from wine_recommendation.parser.base import WineSource

logger = logging.getLogger(__name__)


class ParserService:
    def __init__(self, source: WineSource, repository: Repository) -> None:
        self.source = source
        self.repository = repository

    def update(self) -> int:
        logger.info("Parser update started", extra={"source": self.source.name})
        items = self.source.fetch()
        count = self.repository.upsert_wines(items, self.source.name)
        logger.info("Parser update finished: %d items", count)
        return count
