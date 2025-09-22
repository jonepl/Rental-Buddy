from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)


class ErrorCode(str, Enum):
    INVALID_INPUT = "400_INVALID_INPUT"
    NO_RESULTS = "404_NO_RESULTS"
    VALIDATION_ERROR = "422_VALIDATION_ERROR"
    RATE_LIMITED = "429_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "502_PROVIDER_UNAVAILABLE"


class CompsRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_miles: float = Field(default=5.0, gt=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., gt=0)
    days_old: str = Field(default="*:270")

    @field_validator("bathrooms")
    @classmethod
    def validate_bathrooms(cls, v: float) -> float:
        # Bathrooms must be in 0.5 increments
        if v % 0.5 != 0:
            raise ValueError("Bathrooms must be in 0.5 increments (e.g., 1, 1.5, 2)")
        return v

    @model_validator(mode="after")
    def validate_location_input(self) -> "CompsRequest":
        # Must provide either address OR lat/lng
        if not self.address and (self.latitude is None or self.longitude is None):
            raise ValueError("Must provide either address or latitude & longitude")
        return self


class CompProperty(BaseModel):
    address: str
    price: int
    bedrooms: int
    bathrooms: float
    square_footage: Optional[int] = None
    distance_miles: float = Field(
        ..., description="Distance in miles, rounded to 1 decimal"
    )


class InputSummary(BaseModel):
    resolved_address: str
    latitude: float
    longitude: float
    bedrooms: int
    bathrooms: float
    radius_miles: float
    days_old: str


class CompsResponse(BaseModel):
    input: InputSummary
    comps: List[CompProperty]


class ErrorResponse(BaseModel):
    code: ErrorCode
    message: str
