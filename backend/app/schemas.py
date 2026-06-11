from pydantic import BaseModel, Field


class EstimateCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=250)
    locale: str = Field(default="ru", pattern="^(ru|fr)$")
    vat_pct: float = Field(default=20, ge=0, le=30)


class EstimateUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=250)
    locale: str | None = Field(default=None, pattern="^(ru|fr)$")
    vat_pct: float | None = Field(default=None, ge=0, le=30)


class OpeningPayload(BaseModel):
    kind: str = Field(pattern="^(window|door)$")
    width_m: float = Field(ge=0.1, le=10)
    height_m: float = Field(ge=0.1, le=10)
    count: int = Field(default=1, ge=1, le=20)


class RoomWorkPayload(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    layers: int = Field(ge=1, le=5)
    unit_price: float | None = Field(default=None, ge=0, le=1000)
    quantity: float | None = Field(default=None, ge=0)


class RoomPayload(BaseModel):
    name: str = Field(default="", max_length=80)
    length_m: float = Field(ge=0.5, le=50)
    width_m: float = Field(ge=0.5, le=50)
    height_m: float = Field(ge=1.5, le=10)
    include_ceiling: bool = True
    openings: list[OpeningPayload] = Field(default_factory=list)
    works: list[RoomWorkPayload] = Field(default_factory=list, min_length=1)
