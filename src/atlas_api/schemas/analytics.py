from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioPositionAnalyticsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(
        max_length=10, min_length=1, description="The ticker symbol of the security"
    )
    shares: Decimal = Field(gt=0, description="The number of shares for the position")
    average_cost: Decimal = Field(
        ge=0, description="The average cost per share for the position"
    )
    current_price: Decimal = Field(
        ge=0, description="The current market price per share for the position"
    )
    market_value: Decimal = Field(
        ge=0, description="The total market value of the position"
    )
    cost_basis: Decimal = Field(
        ge=0, description="The total cost basis of the position"
    )
    unrealized_gain_loss: Decimal = Field(
        description="The unrealized gain or loss for the position"
    )
    unrealized_gain_loss_percent: Decimal | None = Field(
        default=None,
        description="The unrealized gain or loss percentage for the position",
    )
    allocation_percent: Decimal = Field(
        description="The allocation percentage of the position within the portfolio"
    )


class PortfolioAnalyticsRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portfolio_id: UUID
    total_market_value: Decimal = Field(
        ge=0, description="The total market value of the portfolio"
    )
    total_cost_basis: Decimal = Field(
        ge=0, description="The total cost basis of the portfolio"
    )
    total_unrealized_gain_loss: Decimal = Field(
        description="The total unrealized gain or loss of the portfolio"
    )
    total_unrealized_gain_loss_percent: Decimal | None = Field(
        default=None,
        description="The total unrealized gain or loss percentage of the portfolio",
    )
    positions: list[PortfolioPositionAnalyticsRead] = Field(
        description="The list of positions within the portfolio"
    )
