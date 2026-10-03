from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Color(StrEnum):
    RED = "red"
    WHITE = "white"
    ROSE = "rose"


class SugarType(StrEnum):
    DRY = "dry"
    SEMI_DRY = "semi_dry"
    SEMI_SWEET = "semi_sweet"
    SWEET = "sweet"


class WineQuery(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    color: Color | None = None
    sugar_type: SugarType | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)

    @model_validator(mode="after")
    def valid_range(self) -> "WineQuery":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("Минимальная цена не может быть выше максимальной")
        return self
