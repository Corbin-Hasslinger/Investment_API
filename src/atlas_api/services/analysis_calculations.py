
from decimal import Decimal
from uuid import UUID

from atlas_api.schemas.analytics import (
    PortfolioAnalyticsRead,
    PortfolioPositionAnalyticsRead,
)

MONEY_PRECISION = Decimal("0.01")


class AnalysisCalculations:
    def __init__(self):
        pass

    @staticmethod
    def round_money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_PRECISION)

    @staticmethod
    def calculate_unrealized_gain_loss(current_price: Decimal, average_cost: Decimal, shares: Decimal) -> Decimal:
        return AnalysisCalculations.round_money((current_price - average_cost) * shares)

    @staticmethod
    def calculate_market_value(current_price: Decimal, shares: Decimal) -> Decimal:
        return AnalysisCalculations.round_money(current_price * shares)
    
    @staticmethod
    def calculate_unrealized_gain_loss_percent(unrealized_gain_loss: Decimal, cost_basis: Decimal) -> Decimal | None:
        if cost_basis == 0:
            return None
        return AnalysisCalculations.round_money((unrealized_gain_loss / cost_basis) * 100)

    @staticmethod
    def calculate_allocation_percent(position_market_value: Decimal, total_market_value: Decimal) -> Decimal:
        if total_market_value == 0:
            return Decimal("0.00")
        return AnalysisCalculations.round_money((position_market_value / total_market_value) * 100)

    @staticmethod
    def calculate_cost_basis(shares: Decimal, average_cost: Decimal) -> Decimal:
        return AnalysisCalculations.round_money(shares * average_cost)
    
    def calculate_position_analytics(
            self,
            symbol: str,
            shares: Decimal,
            average_cost: Decimal,
            current_price: Decimal,
    ) -> PortfolioPositionAnalyticsRead:
        raw_cost_basis = shares * average_cost
        raw_market_value = current_price * shares
        raw_unrealized_gain_loss = raw_market_value - raw_cost_basis

        cost_basis = self.round_money(raw_cost_basis)
        market_value = self.round_money(raw_market_value)
        unrealized_gain_loss = self.round_money(raw_unrealized_gain_loss)
        unrealized_gain_loss_percent = self.calculate_unrealized_gain_loss_percent(
            raw_unrealized_gain_loss,
            raw_cost_basis,
        )
        return PortfolioPositionAnalyticsRead(
            symbol=symbol,
            shares=shares,
            average_cost=average_cost,
            current_price=self.round_money(current_price),
            market_value=market_value,
            cost_basis=cost_basis,
            unrealized_gain_loss=unrealized_gain_loss,
            unrealized_gain_loss_percent=unrealized_gain_loss_percent,
            allocation_percent=Decimal("0.00"),
        )

            
    def calculate_portfolio_analytics(
            self,
            portfolio_id: UUID,
            positions: list[PortfolioPositionAnalyticsRead],
    ) -> PortfolioAnalyticsRead:
        total_market_value = self.round_money(
            sum((position.market_value for position in positions), Decimal(0))
        )
        total_cost_basis = self.round_money(
            sum((position.cost_basis for position in positions), Decimal(0))
        )
        total_unrealized_gain_loss = self.round_money(total_market_value - total_cost_basis)
        total_unrealized_gain_loss_percent = self.calculate_unrealized_gain_loss_percent(
            total_unrealized_gain_loss,
            total_cost_basis,
        )
        ordered_positions = sorted(positions, key=lambda position: position.symbol)
        positions_with_allocations = [
            position.model_copy(
                update={
                    "allocation_percent": self.calculate_allocation_percent(
                        position.market_value,
                        total_market_value,
                    )
                }
            )
            for position in ordered_positions
        ]
        return PortfolioAnalyticsRead(
            portfolio_id=portfolio_id,
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_gain_loss=total_unrealized_gain_loss,
            total_unrealized_gain_loss_percent=total_unrealized_gain_loss_percent,
            positions=positions_with_allocations,
        )
        