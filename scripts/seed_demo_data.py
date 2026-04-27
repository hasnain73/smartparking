import asyncio
import os
import sys

# Ensure parkr is importable if run from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select
from parkr.database import AsyncSessionLocal
from parkr.models.enums import ParkingType, PrivateStatus, SpotType, StreetStatus
from parkr.models.parking_spot import ParkingSpot
from parkr.models.spot_signal import SignalType, SourceType, SpotSignal
from parkr.models.spot_verification import SpotVerification


async def seed():
    async with AsyncSessionLocal() as session:
        # Fetch existing demo spot IDs
        result = await session.execute(
            select(ParkingSpot.id).where(ParkingSpot.address.startswith("Demo "))
        )
        demo_ids = result.scalars().all()

        if demo_ids:
            # Delete in order to avoid FK issues
            await session.execute(delete(SpotSignal).where(SpotSignal.spot_id.in_(demo_ids)))
            await session.execute(delete(SpotVerification).where(SpotVerification.spot_id.in_(demo_ids)))
            await session.execute(delete(ParkingSpot).where(ParkingSpot.id.in_(demo_ids)))
            await session.flush()

        spots = []

        # 5 street spots
        for i in range(5):
            lat = 12.9716 + (i * 0.001)
            lng = 77.5946 + (i * 0.001)
            spot = ParkingSpot(
                parking_type=ParkingType.street,
                location=f"SRID=4326;POINT({lng} {lat})",
                spot_type=SpotType.hatchback,
                address=f"Demo Street Spot {i}",
                street_status=StreetStatus.unknown,
                private_status=None,
            )
            spots.append(spot)

        # 5 private spots
        for i in range(5):
            lat = 12.9716 - (i * 0.001)
            lng = 77.5946 - (i * 0.001)
            spot = ParkingSpot(
                parking_type=ParkingType.private,
                location=f"SRID=4326;POINT({lng} {lat})",
                spot_type=SpotType.sedan,
                address=f"Demo Private Spot {i}",
                private_status=PrivateStatus.free,
                street_status=None,
                price_per_hour_paise=2000,
                max_duration_hrs=2,
            )
            spots.append(spot)

        session.add_all(spots)
        await session.flush()

        signals = []
        for index, spot in enumerate(spots):
            if index < 3:
                # mostly free
                seq = [SignalType.free, SignalType.free, SignalType.free, SignalType.free, SignalType.occupied]
            elif index < 6:
                # mostly occupied
                seq = [SignalType.occupied, SignalType.occupied, SignalType.occupied, SignalType.occupied, SignalType.free]
            else:
                # mixed
                seq = [SignalType.free, SignalType.occupied, SignalType.free, SignalType.occupied]

            for s_type in seq:
                signal = SpotSignal(
                    spot_id=spot.id,
                    signal_type=s_type,
                    source_type=SourceType.user,
                    confidence_score=0.8,
                )
                signals.append(signal)

        session.add_all(signals)
        await session.commit()
        
        print("Demo data seeded successfully")


if __name__ == "__main__":
    asyncio.run(seed())
