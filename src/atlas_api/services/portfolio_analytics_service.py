import asyncio
from uuid import UUID

from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.repositories.position_repository import PositionRepository
from atlas_api.schemas.analytics import PortfolioAnalyticsRead
from atlas_api.services.analysis_calculations import AnalysisCalculations
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.tools import PortfolioNotFoundError


class PortfolioAnalyticsService:
    def __init__(
        self,
        analysis_calculations: AnalysisCalculations,
        portfolio_repository: PortfolioRepository,
        position_repository: PositionRepository,
        market_data_service: MarketDataService,
    ):
        self.analysis_calculations = analysis_calculations
        self.portfolio_repository = portfolio_repository
        self.position_repository = position_repository
        self.market_data_service = market_data_service

    def verify_portfolio_ownership(self, portfolio_id: UUID, user_id: UUID) -> bool:
        portfolio = self.portfolio_repository.get_portfolio_by_id(portfolio_id, user_id)
        return portfolio is not None and portfolio.user_id == user_id

    async def get_portfolio_analytics(
        self, portfolio_id: UUID, user_id: UUID
    ) -> PortfolioAnalyticsRead:
        if not self.verify_portfolio_ownership(portfolio_id, user_id):
            raise PortfolioNotFoundError(
                "User does not have ownership of the portfolio."
            )

        positions = self.position_repository.get_all_positions(portfolio_id)
        if not positions:
            return self.analysis_calculations.calculate_portfolio_analytics(
                portfolio_id, []
            )

        async def calculate_position(position):
            position_quote = await self.market_data_service.get_quote(position.symbol)
            return self.analysis_calculations.calculate_position_analytics(
                position.symbol,
                position.shares,
                position.average_cost,
                position_quote.current_price,
            )

        position_analytics = await asyncio.gather(
            *(calculate_position(position) for position in positions)
        )
        return self.analysis_calculations.calculate_portfolio_analytics(
            portfolio_id, position_analytics
        )
