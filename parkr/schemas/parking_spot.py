from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from parkr.models.enums import ParkingType, PrivateStatus, SpotType, StreetStatus


# ── Shared ────────────────────────────────────────────────────────────────────

class LatLng(BaseModel):
    lat: Annotated[float, Field(ge=-90, le=90)]
    lng: Annotated[float, Field(ge=-180, le=180)]


# ── Create request schemas (discriminated union on parking_type) ───────────────

class CreatePrivateSpot(BaseModel):
    parking_type: Literal[ParkingType.private]
    lat: Annotated[float, Field(ge=-90, le=90)]
    lng: Annotated[float, Field(ge=-180, le=180)]
    spot_type: SpotType = SpotType.hatchback
    address: str | None = None
    # Private-only fields
    price_per_hour_paise: Annotated[int, Field(gt=0)]
    max_duration_hrs: Annotated[int, Field(ge=1, le=5)] = 5

    model_config = {"json_schema_extra": {"example": {
        "parking_type": "private",
        "lat": 12.9716,
        "lng": 77.5946,
        "spot_type": "hatchback",
        "address": "12 MG Road, Bangalore",
        "price_per_hour_paise": 5000,
        "max_duration_hrs": 3,
    }}}


class CreateStreetSpot(BaseModel):
    parking_type: Literal[ParkingType.street]
    lat: Annotated[float, Field(ge=-90, le=90)]
    lng: Annotated[float, Field(ge=-180, le=180)]
    spot_type: SpotType = SpotType.hatchback
    address: str | None = None
    # Street spots start as UNKNOWN — no price, no duration
    initial_status: StreetStatus = StreetStatus.unknown

    model_config = {"json_schema_extra": {"example": {
        "parking_type": "street",
        "lat": 12.9710,
        "lng": 77.5940,
        "spot_type": "sedan",
        "address": "Near Cubbon Park Gate 2",
    }}}


# Union type — FastAPI will validate against whichever discriminator matches
CreateSpotRequest = CreatePrivateSpot | CreateStreetSpot


# ── Response schemas ──────────────────────────────────────────────────────────

class SpotResponse(BaseModel):
    id: uuid.UUID
    parking_type: ParkingType
    lat: float
    lng: float
    spot_type: SpotType
    address: str | None

    # Status: only the relevant field is populated
    private_status: PrivateStatus | None = None
    street_status: StreetStatus | None = None

    # Street-only display label (never shown for private)
    display_label: str | None = None

    # Private-only pricing
    price_per_hour_paise: int | None = None
    max_duration_hrs: int | None = None

    confidence_score: float | None = None
    is_active: bool
    created_at: datetime
    status_updated_at: datetime

    # Set by the geo query — distance from requested point
    distance_m: float | None = None

    model_config = {"from_attributes": True}


class NearbySpotResponse(BaseModel):
    """Wrapper that makes the response contract explicit."""
    spots: list[SpotResponse]
    total: int
    query_lat: float
    query_lng: float
    radius_m: int