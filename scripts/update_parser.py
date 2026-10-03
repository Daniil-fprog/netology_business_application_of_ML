from wine_recommendation.core.config import settings
from wine_recommendation.db.repositories import Repository
from wine_recommendation.db.session import SessionLocal
from wine_recommendation.parser.perekrestok import PerekrestokSource
from wine_recommendation.parser.service import ParserService


def main() -> None:
    if not settings.parser_enabled:
        raise SystemExit("Check source terms, then set PARSER_ENABLED=true")
    source = PerekrestokSource(
        settings.perekrestok_api_url, settings.parser_timeout, settings.parser_user_agent
    )
    with SessionLocal() as session:
        ParserService(source, Repository(session)).update()


if __name__ == "__main__":
    main()
