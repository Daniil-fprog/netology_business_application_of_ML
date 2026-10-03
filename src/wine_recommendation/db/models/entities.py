from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wine_recommendation.db.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    likes: Mapped[list[UserLike]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Wine(TimestampMixin, Base):
    __tablename__ = "wines"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(255))
    color: Mapped[str | None] = mapped_column(String(32), index=True)
    sugar_type: Mapped[str | None] = mapped_column(String(32), index=True)
    grape: Mapped[str | None] = mapped_column(String(255))
    volume: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    product_url: Mapped[str | None] = mapped_column(Text)
    offers: Mapped[list[WineOffer]] = relationship(
        back_populates="wine", cascade="all, delete-orphan"
    )


class WineOffer(Base):
    __tablename__ = "wine_offers"
    __table_args__ = (UniqueConstraint("wine_id", "source", name="uq_offer_wine_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    wine_id: Mapped[int] = mapped_column(ForeignKey("wines.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(80), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    external_rating: Mapped[float | None] = mapped_column(Float)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    product_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    wine: Mapped[Wine] = relationship(back_populates="offers")


class UserLike(Base):
    __tablename__ = "user_likes"
    __table_args__ = (UniqueConstraint("user_id", "wine_id", name="uq_user_like"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    wine_id: Mapped[int] = mapped_column(ForeignKey("wines.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user: Mapped[User] = relationship(back_populates="likes")


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    raw_query: Mapped[str] = mapped_column(Text)
    parsed_params: Mapped[dict[str, Any]] = mapped_column(JSON)
    recommended_wine_ids: Mapped[list[int]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
