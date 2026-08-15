

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PositionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    security_id: UUID
    shares: Decimal = Field(gt=0, description="The number of shares for the position")
    average_cost: Decimal = Field(ge=0, description="The average price per share for the position")


class PositionRead(PositionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

class PositionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shares: Decimal | None = Field(default=None, gt=0, description="The number of shares for the position")
    average_cost: Decimal | None = Field(default=None, ge=0, description="The average price per share for the position")
