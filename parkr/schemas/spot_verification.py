from datetime import datetime
from pydantic import BaseModel
from parkr.models.spot_verification import VerificationStatus

class VerifySpotRequest(BaseModel):
    status: VerificationStatus

from uuid import UUID

class VerifySpotResponse(BaseModel):
    id: int
    spot_id: UUID
    status: VerificationStatus
    created_at: datetime
    
    model_config = {"from_attributes": True}
