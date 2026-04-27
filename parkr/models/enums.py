from enum import Enum

class ParkingType(str, Enum):
    private = "private"
    street = "street"

class SpotType(str, Enum):
    hatchback = "hatchback"
    sedan = "sedan"
    suv = "suv"
    two_wheeler = "two_wheeler"
    structured = "structured"

class PrivateStatus(str, Enum):
    free = "free"
    reserved = "reserved"
    occupied = "occupied"

class StreetStatus(str, Enum):
    unknown = "unknown"
    likely_free = "likely_free"
    likely_occupied = "likely_occupied"
