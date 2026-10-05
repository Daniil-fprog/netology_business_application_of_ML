from wine_recommendation.core.config import settings
from wine_recommendation.db.repositories import Repository
from wine_recommendation.db.session import SessionLocal
from wine_recommendation.parser.mock_json import MockJsonSource
from wine_recommendation.parser.service import ParserService


def main() -> None:
    if not settings.parser_enabled:
        raise SystemExit("Check source terms, then set PARSER_ENABLED=true")
    source = MockJsonSource(settings.mock_json_data)
    with SessionLocal() as session:
        ParserService(source, Repository(session)).update()


if __name__ == "__main__":
    main()
