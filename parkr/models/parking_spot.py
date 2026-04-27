import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from parkr.database import Base
from parkr.models.enums import ParkingType, PrivateStatus, SpotType, StreetStatus


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    # ── Identity ──────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Parking type (the fundamental separator) ──────────────────
    parking_type: Mapped[ParkingType] = mapped_column(
        Enum(ParkingType, name="parking_type_enum"), nullable=False, index=True
    )

    # ── Geospatial fallback ───────────────────────────────────────
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geohash6: Mapped[str] = mapped_column(String(8), nullable=True, index=True)

    address: Mapped[str | None] = mapped_column(String(300))

    # ── Vehicle compatibility ─────────────────────────────────────
    spot_type: Mapped[SpotType] = mapped_column(
        Enum(SpotType, name="spot_type_enum"),
        nullable=False,
        default=SpotType.hatchback,
    )

    # ── Status: EXACTLY ONE is non-NULL per row ───────────────────
    # private_status is set ↔ parking_type = 'private'
    # street_status  is set ↔ parking_type = 'street'
    # Enforced by the CHECK constraint below AND by @validates below.
    private_status: Mapped[PrivateStatus | None] = mapped_column(
        Enum(PrivateStatus, name="private_status_enum"), nullable=True
    )
    street_status: Mapped[StreetStatus | None] = mapped_column(
        Enum(StreetStatus, name="street_status_enum"), nullable=True
    )

    # ── Confidence / freshness (street spots only) ────────────────
    confidence_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    status_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Private-spot reservation config ──────────────────────────
    price_per_hour_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_duration_hrs: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Metadata ─────────────────────────────────────────────────
    ai_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── DB-level CHECK constraint ─────────────────────────────────
    # This is the hard enforcement layer. Even a raw SQL INSERT that
    # violates the private/street separation will be rejected by Postgres.
    __table_args__ = (
        CheckConstraint(
            """
            (parking_type = 'private'
                AND private_status IS NOT NULL
                AND street_status  IS NULL)
            OR
            (parking_type = 'street'
                AND street_status  IS NOT NULL
                AND private_status IS NULL)
            """,
            name="chk_status_matches_parking_type",
        ),
        CheckConstraint(
            "NOT (parking_type = 'street' AND max_duration_hrs IS NOT NULL)",
            name="chk_no_duration_for_street",
        ),
        CheckConstraint(
            "NOT (parking_type = 'street' AND price_per_hour_paise IS NOT NULL)",
            name="chk_no_price_for_street",
        ),
        # Partial index: private spots by status
        Index(
            "idx_spots_private_status",
            "parking_type",
            "private_status",
            postgresql_where=text("parking_type = 'private' AND is_active = true"),
        ),
        # Partial index: street spots by status
        Index(
            "idx_spots_street_status",
            "parking_type",
            "street_status",
            postgresql_where=text("parking_type = 'street' AND is_active = true"),
        ),
    )

    # ── Application-level validation (second enforcement layer) ───
    @validates("parking_type", "private_status", "street_status")
    def validate_status_matches_type(self, key, value):
        """Raise at the ORM layer before even touching the DB."""
        if key == "private_status" and value is not None:
            if self.parking_type == ParkingType.street:
                raise ValueError(
                    "Cannot set private_status on a street parking spot."
                )
        if key == "street_status" and value is not None:
            if self.parking_type == ParkingType.private:
                raise ValueError(
                    "Cannot set street_status on a private parking spot."
                )
        return value

    def __repr__(self) -> str:
        status = self.private_status or self.street_status
        return f"<ParkingSpot id={self.id} type={self.parking_type} status={status}>" 