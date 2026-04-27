import random
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from parkr.database import SessionLocal
from parkr.models.parking_spot import ParkingSpot
from parkr.models.spot_signal import SpotSignal, SignalType, SourceType
from parkr.models.enums import ParkingType, PrivateStatus, StreetStatus, SpotType

def seed_demo_data(db: Session = None):
    """
    Seeds 20 demo parking spots near Dharwad (Manjushree Nagar).
    Safe to run multiple times.
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # Check if we already have demo data to avoid duplicates
        existing_count = db.query(ParkingSpot).count()
        if existing_count >= 20:
            print(f"Skipping seeding: {existing_count} spots already exist.")
            return

        print("Seeding demo data...")
        center_lat = 15.4589
        center_lng = 75.0078

        # Demo data types and labels
        parking_types = [ParkingType.street, ParkingType.private]
        spot_types = [SpotType.hatchback, SpotType.sedan, SpotType.suv, SpotType.two_wheeler, SpotType.structured]

        for i in range(20):
            # Random offset ± 0.002
            lat_offset = (random.random() - 0.5) * 0.004
            lng_offset = (random.random() - 0.5) * 0.004
            
            p_type = random.choice(parking_types)
            s_type = random.choice(spot_types)
            
            # If spot_type is structured, force some settings for demo logic
            if s_type == SpotType.structured:
                p_type = ParkingType.private # Structured is usually private/paid
            
            spot = ParkingSpot(
                id=uuid.uuid4(),
                parking_type=p_type,
                latitude=center_lat + lat_offset,
                longitude=center_lng + lng_offset,
                spot_type=s_type,
                address=f"Demo Location {i+1}, Manjushree Nagar",
                is_active=True,
                # Set statuses based on type
                private_status=PrivateStatus.free if p_type == ParkingType.private else None,
                street_status=StreetStatus.unknown if p_type == ParkingType.street else None,
                # Pricing for private spots
                price_per_hour_paise=random.choice([3000, 5000, 8000]) if p_type == ParkingType.private else None,
                max_duration_hrs=random.choice([2, 3, 4]) if p_type == ParkingType.private else None
            )
            
            db.add(spot)
            db.flush() # Get ID if needed, though we set it
            
            # Create a corresponding signal
            signal = SpotSignal(
                spot_id=spot.id,
                signal_type=random.choice([SignalType.free, SignalType.occupied]),
                confidence_score=round(random.uniform(0.6, 0.95), 2),
                source_type=SourceType.passive, # Simulate demo seed as passive detection
            )
            db.add(signal)

        db.commit()
        print("Demo data seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_demo_data()
