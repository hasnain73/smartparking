from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from parkr.database import Base


class SignalType(str, enum.Enum):
    free = "free"
    occupied = "occupied"


class SourceType(str, enum.Enum):
    user = "user"
    passive = "passive"


class SpotSignal(Base):
    __tablename__ = "spot_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parking_spots.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
