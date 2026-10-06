from __future__ import annotations

from collections import Counter

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from wine_recommendation.db.models import RecommendationEvent, User, UserLike, Wine, WineOffer
from wine_recommendation.parser.schemas import ParsedWine
from wine_recommendation.recommendation.schemas import WineCandidate


class ConflictError(ValueError):
    pass


class NotFoundError(ValueError):
    pass


class Repository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, external_id: str, username: str | None) -> User:
        user = User(external_id=external_id, username=username)
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Пользователь с таким external_id уже существует") from exc
        self.session.refresh(user)
        return user

    def get_user(self, user_id: int) -> User:
        user = self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден")
        return user

    def list_users(self, offset: int = 0, limit: int = 100) -> list[User]:
        return list(
            self.session.scalars(select(User).order_by(User.id).offset(offset).limit(limit))
        )

    def get_wine(self, wine_id: int) -> Wine:
        wine = self.session.scalar(
            select(Wine).options(selectinload(Wine.offers)).where(Wine.id == wine_id)
        )
        if wine is None:
            raise NotFoundError("Вино не найдено")
        return wine

    def list_wines(self, offset: int = 0, limit: int = 100) -> list[Wine]:
        return list(
            self.session.scalars(
                select(Wine)
                .options(selectinload(Wine.offers))
                .order_by(Wine.id)
                .offset(offset)
                .limit(limit)
            )
        )

    def add_like(self, user_id: int, wine_id: int) -> UserLike:
        self.get_user(user_id)
        self.get_wine(wine_id)
        like = UserLike(user_id=user_id, wine_id=wine_id)
        self.session.add(like)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Лайк уже существует") from exc
        self.session.refresh(like)
        return like

    def remove_like(self, user_id: int, wine_id: int) -> None:
        result = self.session.execute(
            delete(UserLike).where(UserLike.user_id == user_id, UserLike.wine_id == wine_id)
        )
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise NotFoundError("Лайк не найден")
        self.session.commit()

    def candidates(self) -> list[WineCandidate]:
        rows = self.session.execute(
            select(Wine, WineOffer).join(WineOffer).where(WineOffer.is_available.is_(True))
        ).all()
        return [
            WineCandidate(
                wine_id=wine.id,
                name=wine.name,
                color=wine.color,
                sugar_type=wine.sugar_type,
                price=float(offer.price),
                rating=offer.external_rating,
                reviews_count=offer.reviews_count,
                brand=wine.brand,
                country=wine.country,
                grape=wine.grape,
                image_url=wine.image_url,
                product_url=offer.product_url or wine.product_url,
            )
            for wine, offer in rows
        ]

    def preferred_pair(self, user_id: int) -> tuple[str, str] | None:
        rows = self.session.execute(
            select(Wine.color, Wine.sugar_type)
            .join(UserLike, UserLike.wine_id == Wine.id)
            .where(UserLike.user_id == user_id)
        ).all()
        pairs = [(color, sugar) for color, sugar in rows if color and sugar]
        return Counter(pairs).most_common(1)[0][0] if pairs else None

    def liked_wine_ids(self, user_id: int) -> set[int]:
        return set(
            self.session.scalars(select(UserLike.wine_id).where(UserLike.user_id == user_id))
        )

    def likes_by_user(self) -> dict[int, set[int]]:
        result: dict[int, set[int]] = {}
        for user_id, wine_id in self.session.execute(select(UserLike.user_id, UserLike.wine_id)):
            result.setdefault(user_id, set()).add(wine_id)
        return result

    def save_event(
        self, user_id: int | None, raw_query: str, parsed: dict[str, object], wine_ids: list[int]
    ) -> None:
        self.session.add(
            RecommendationEvent(
                user_id=user_id,
                raw_query=raw_query,
                parsed_params=parsed,
                recommended_wine_ids=wine_ids,
            )
        )
        self.session.commit()

    def upsert_wines(self, items: list[ParsedWine], source: str) -> int:
        seen: set[int] = set()
        for item in items:
            wine = self.session.scalar(select(Wine).where(Wine.external_id == item.external_id))
            values = item.wine_values()
            if wine is None:
                wine = Wine(external_id=item.external_id, **values)
                self.session.add(wine)
                self.session.flush()
            else:
                for key, value in values.items():
                    setattr(wine, key, value)
            offer = self.session.scalar(
                select(WineOffer).where(WineOffer.wine_id == wine.id, WineOffer.source == source)
            )
            offer_values = item.offer_values()
            if offer is None:
                offer = WineOffer(wine_id=wine.id, source=source, **offer_values)
                self.session.add(offer)
            else:
                for key, value in offer_values.items():
                    setattr(offer, key, value)
            seen.add(wine.id)

        # Products absent from a successful full snapshot become unavailable.
        offers = self.session.scalars(select(WineOffer).where(WineOffer.source == source))
        for offer in offers:
            if offer.wine_id not in seen:
                offer.is_available = False
        self.session.commit()
        return len(items)
