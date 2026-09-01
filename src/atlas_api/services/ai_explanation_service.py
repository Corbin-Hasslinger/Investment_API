from datetime import UTC, datetime
from uuid import UUID

from atlas_api.ai.context import build_portfolio_ai_context, build_security_ai_context
from atlas_api.ai.prompts import (
    build_portfolio_explanation_prompt,
    build_security_explanation_prompt,
)
from atlas_api.clients.llm_client import LLMClient
from atlas_api.schemas.ai import (
    PortfolioExplanationContent,
    PortfolioExplanationRead,
    SecurityExplanationContent,
    SecurityExplanationRead,
)
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.research_service import ResearchService


class AIExplanationService:
    """Service for generating AI explanations for portfolios and securities."""

    def __init__(
        self,
        llm_client: LLMClient,
        portfolio_service: PortfolioService,
        portfolio_analytics_service: PortfolioAnalyticsService,
        research_service: ResearchService,
        market_data_service: MarketDataService,
    ):
        self.llm_client = llm_client
        self.portfolio_service = portfolio_service
        self.portfolio_analytics_service = portfolio_analytics_service
        self.research_service = research_service
        self.market_data_service = market_data_service

    async def explain_portfolio(
        self, portfolio_id: UUID, user_id: UUID
    ) -> PortfolioExplanationRead:
        context = await build_portfolio_ai_context(
            portfolio_id=portfolio_id,
            user_id=user_id,
            portfolio_service=self.portfolio_service,
            portfolio_analytics_service=self.portfolio_analytics_service,
        )
        prompt = build_portfolio_explanation_prompt(context)
        explanation = await self.llm_client.generate_structured(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            output_type=PortfolioExplanationContent,
        )
        generated_at = datetime.now(UTC)
        return PortfolioExplanationRead(
            portfolio_id=portfolio_id,
            data_retrieved_at=context.data_retrieved_at,
            generated_at=generated_at,
            explanation=explanation,
        )

    async def explain_security(
        self,
        symbol: str,
    ) -> SecurityExplanationRead:
        context = await build_security_ai_context(
            symbol=symbol,
            market_data_service=self.market_data_service,
            research_service=self.research_service,
        )
        prompt = build_security_explanation_prompt(context)
        explanation = await self.llm_client.generate_structured(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            output_type=SecurityExplanationContent,
        )
        generated_at = datetime.now(UTC)
        return SecurityExplanationRead(
            symbol=context.symbol,
            data_retrieved_at=context.data_retrieved_at,
            generated_at=generated_at,
            explanation=explanation,
        )
