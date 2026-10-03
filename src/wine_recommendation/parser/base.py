from typing import Protocol

from wine_recommendation.parser.schemas import ParsedWine


class SourceError(RuntimeError):
    pass


class WineSource(Protocol):
    name: str

    def fetch(self) -> list[ParsedWine]: ...
