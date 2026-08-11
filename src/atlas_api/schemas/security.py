
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityCreate(BaseModel):
    name: str = Field(max_length=100, min_length=1, description="The name of the security")
    symbol: str = Field(max_length=5, min_length=1, description="The ticker symbol of the security")
    exchange: str = Field(max_length=50, min_length=1, description="The exchange where the security is traded")
    currency: str = Field(max_length=10, min_length=1, description="The currency of the security")

class SecurityRead(SecurityCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

class SecurityUpdate(BaseModel):
    exchange: str | None = Field(default=None, max_length=50, min_length=1, description="The exchange where the security is traded")
    currency: str | None = Field(default=None, max_length=10, min_length=1, description="The currency of the security")
    name: str | None = Field(default=None, max_length=100, min_length=1, description="The name of the security")