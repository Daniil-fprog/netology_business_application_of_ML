from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from wine_recommendation.query_parser.schemas import WineQuery


class UserCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=255)
    username: str | None = Field(default=None, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    username: str | None
    created_at: datetime


class LikeCreate(BaseModel):
    wine_id: int = Field(gt=0)


class LikeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    wine_id: int
    created_at: datetime


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    price: Decimal
    old_price: Decimal | None
    is_available: bool
    external_rating: float | None
    reviews_count: int
    product_url: str | None


class WineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    name: str
    brand: str | None
    country: str | None
    region: str | None
    color: str | None
    sugar_type: str | None
    grape: str | None
    volume: float | None
    description: str | None
    image_url: str | None
    product_url: str | None
    offers: list[OfferRead]


class RecommendationRequest(BaseModel):
    user_id: int | None = Field(default=None, gt=0)
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=50)


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    wine_id: int
    name: str
    price: float
    rating: float | None
    color: str | None
    sugar_type: str | None
    brand: str | None
    country: str | None
    grape: str | None
    image_url: str | None
    product_url: str | None
    score: float


class RecommendationResponse(BaseModel):
    parsed_query: WineQuery
    recommendation_mode: Literal["standard", "ml"]
    recommendations: list[RecommendationRead]


class ParserUpdateResponse(BaseModel):
    source: str
    updated: int


class MLTrainingResponse(BaseModel):
    status: Literal["trained"] = "trained"
    trained_at: datetime
    wines_count: int
    users_count: int
    likes_count: int
