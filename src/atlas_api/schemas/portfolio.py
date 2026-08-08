
import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioCreate(BaseModel):
    name: str = Field(max_length=50, min_length=1, description="The name of the portfolio")
    description: str | None = Field(default=None, max_length=500, description="A brief description of the portfolio")

class PortfolioRead(PortfolioCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

class PortfolioUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(default=None, max_length=50, min_length=1, description="The name of the portfolio")
    description: str | None = Field(default=None, max_length=500, description="A brief description of the portfolio")