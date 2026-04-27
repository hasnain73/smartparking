from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_AsText, ST_DWithin, ST_Distance
from fastapi import UploadFile, File
from parkr.services.cv_detector import detect_parking_status

from parkr.database import get_db
from parkr.models.enums import ParkingType, PrivateStatus, StreetStatus, SpotType
from parkr.models.parking_spot import ParkingSpot
from parkr.models.spot_signal import SignalType, SourceType, SpotSignal
from parkr.models.spot_verification import SpotVerification
from parkr.schemas.parking_spot import (
    CreatePrivateSpot,
    CreateSpotRequest,
    CreateStreetSpot,
    NearbySpotResponse,
    SpotResponse,
)
from parkr.schemas.spot_verification import VerifySpotRequest, VerifySpotResponse

import uuid

router = APIRouter(prefix="/spots", tags=["spots"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_point_wkt(lat: float, lng: float) -> str:
    return f"SRID=4326;POINT({lng} {lat})"


def get_confidence_label(c: float) -> str:
    if c >= 0.7:
        return "likely free"
    elif c <= 0.3:
        return "likely occupied"
    return "uncertain"


def _spot_to_response(spot: ParkingSpot, distance_m: float | None = None) -> SpotResponse:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # SAFE access (NO lazy loading)
    status_updated_at = spot.__dict__.get("status_updated_at", None)

    # Extract lat/lng from WKT
    lat, lng = 0.0, 0.0
    if spot.location:
        wkt = str(spot.location)
        if wkt.startswith("POINT"):
            coords = wkt.replace("POINT(", "").replace(")", "").split()
            lng, lat = float(coords[0]), float(coords[1])

    if spot.parking_type == ParkingType.private:
        if spot.private_status == PrivateStatus.free:
            display_label = "available"
        else:
            display_label = "occupied"
    else:
        display_label = get_confidence_label(spot.confidence_score or 0.5)

    return SpotResponse(
        id=spot.id,
        parking_type=spot.parking_type,
        lat=lat,
        lng=lng,
        spot_type=spot.spot_type,
        address=spot.address,
        private_status=spot.private_status,
        street_status=spot.street_status,
        display_label=display_label,
        price_per_hour_paise=spot.price_per_hour_paise,
        max_duration_hrs=spot.max_duration_hrs,
        confidence_score=spot.confidence_score,
        is_active=spot.is_active,
        created_at=spot.created_at,
        status_updated_at=status_updated_at,  # SAFE
        distance_m=round(distance_m, 1) if distance_m is not None else None,
    )


# ── CREATE SPOT ──────────────────────────────────────────────────────────────

@router.post("", response_model=SpotResponse, status_code=status.HTTP_201_CREATED)
def create_spot(
    body: CreateSpotRequest,
    db: Session = Depends(get_db),
) -> SpotResponse:

    wkt = _make_point_wkt(body.lat, body.lng)

    if isinstance(body, CreatePrivateSpot):
        spot = ParkingSpot(
            parking_type=ParkingType.private,
            location=wkt,
            spot_type=body.spot_type,
            address=body.address,
            private_status=PrivateStatus.free,
            street_status=None,
            price_per_hour_paise=body.price_per_hour_paise,
            max_duration_hrs=body.max_duration_hrs,
        )

    elif isinstance(body, CreateStreetSpot):
        spot = ParkingSpot(
            parking_type=ParkingType.street,
            location=wkt,
            spot_type=body.spot_type,
            address=body.address,
            street_status=body.initial_status,
            private_status=None,
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid parking_type")

    db.add(spot)
    db.flush()
    db.refresh(spot)

    result = db.execute(
        select(
            ParkingSpot,
            ST_AsText(ParkingSpot.location).label("location_wkt"),
        ).where(ParkingSpot.id == spot.id)
    )

    row = result.one()

    # SAFE: assign WKT for parsing (acceptable here)
    row[0].location = row[1]

    return _spot_to_response(row[0])


# ── NEARBY SPOTS (FIXED) ─────────────────────────────────────────────────────

@router.get("/nearby", response_model=NearbySpotResponse)
def get_nearby_spots(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    radius: Annotated[int, Query(ge=50, le=5000)] = 200,
    parking_type: Annotated[ParkingType | None, Query()] = None,
    spot_type: Annotated[SpotType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Session = Depends(get_db),
) -> NearbySpotResponse:

    user_point = func.ST_GeogFromText(f"SRID=4326;POINT({lng} {lat})")

    distance_expr = ST_Distance(ParkingSpot.location, user_point).label("distance_m")

    stmt = (
        select(
            ParkingSpot,
            ST_AsText(ParkingSpot.location).label("location_wkt"),
            distance_expr,
        )
        .where(
            ParkingSpot.is_active.is_(True),
            ST_DWithin(ParkingSpot.location, user_point, radius),
        )
        .order_by(distance_expr)
        .limit(limit)
    )

    if parking_type:
        stmt = stmt.where(ParkingSpot.parking_type == parking_type)

    if spot_type:
        stmt = stmt.where(ParkingSpot.spot_type == spot_type)

    with db.no_autoflush:
        result = db.execute(stmt)
        rows = result.all()

    spots: list[SpotResponse] = []

    for spot, location_wkt, dist in rows:

        # DO NOT mutate ORM object
        location = location_wkt

        signal_result = db.execute(
            select(SpotSignal)
            .where(SpotSignal.spot_id == spot.id)
            .order_by(SpotSignal.created_at.desc())
            .limit(5)
        )

        signals = signal_result.scalars().all()

        score = sum(1 if s.signal_type.value == "free" else -1 for s in signals)

        if signals:
            confidence = (score + len(signals)) / (2 * len(signals))
        else:
            confidence = 0.5

        if len(signals) < 3:
            confidence = (confidence + 0.5) / 2

        confidence = round(max(0.0, min(1.0, confidence)), 2)

        # SAFE inject (not DB tracked)
        spot.__dict__["confidence_score"] = confidence
        spot.__dict__["location"] = location

        spots.append(_spot_to_response(spot, distance_m=dist))

    return NearbySpotResponse(
        spots=spots,
        total=len(spots),
        query_lat=lat,
        query_lng=lng,
        radius_m=radius,
    )


# ── VERIFY SPOT ──────────────────────────────────────────────────────────────

@router.post("/{spot_id}/verify", response_model=VerifySpotResponse)
def verify_spot(
    spot_id: uuid.UUID,
    body: VerifySpotRequest,
    db: Session = Depends(get_db),
):

    spot = db.get(ParkingSpot, spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    verification = SpotVerification(
        spot_id=spot_id,
        status=body.status,
    )

    signal = SpotSignal(
        spot_id=spot_id,
        signal_type=SignalType(body.status.value),
        source_type=SourceType.user,
        confidence_score=0.7,
    )

    db.add(verification)
    db.add(signal)

    db.commit()
    db.refresh(verification)

    return verification


# ── LIST ALL SPOTS ───────────────────────────────────────────────────────────

@router.get("", response_model=list[SpotResponse])
def list_spots(db: Session = Depends(get_db)):

    result = db.execute(
        select(
            ParkingSpot,
            ST_AsText(ParkingSpot.location).label("location_wkt"),
        )
    )

    rows = result.all()

    spots: list[SpotResponse] = []

    for spot, location_wkt in rows:
        spot.__dict__["location"] = location_wkt
        spots.append(_spot_to_response(spot))

    return spots


# ── DETECT SPOT STATUS ───────────────────────────────────────────────────────

@router.post("/detect")
async def detect_spot_status(
    file: UploadFile = File(...),
    spot_id: uuid.UUID | None = None,
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_bytes = await file.read()
        result = detect_parking_status(image_bytes)

        if spot_id:
            spot = db.get(ParkingSpot, spot_id)
            if not spot:
                raise HTTPException(status_code=404, detail="Spot not found")

            signal = SpotSignal(
                spot_id=spot_id,
                signal_type=SignalType(result["status"]),
                source_type=SourceType.passive,
                confidence_score=result["confidence"],
            )

            db.add(signal)
            db.commit()
            db.refresh(signal)

            return {
                "status": result["status"],
                "confidence": result["confidence"],
                "signal_id": str(signal.id),
                "message": "Signal created successfully"
            }

        return {
            "status": result["status"],
            "confidence": result["confidence"],
            "message": "Detection complete (no signal saved)"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")