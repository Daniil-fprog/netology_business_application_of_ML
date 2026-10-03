from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from wine_recommendation.db.repositories import Repository
from wine_recommendation.db.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_repository(session: SessionDep) -> Repository:
    return Repository(session)


RepositoryDep = Annotated[Repository, Depends(get_repository)]
