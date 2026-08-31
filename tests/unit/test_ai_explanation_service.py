from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from atlas_api.ai.prompts import (
    PORTFOLIO_SCHEMA_NAME,
    SECURITY_SCHEMA_NAME,
)
from atlas_api.schemas.ai import (
    PortfolioExplanationContent,
    PortfolioExplanationRead,
    SecurityExplanationContent,
    SecurityExplanationRead,
    StructuredPrompt,
)
from atlas_api.services import ai_explanation_service
from atlas_api.services.ai_explanation_service import AIExplanationService
from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.services.research_service import ResearchService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

PORTFOLIO_ID = uuid4()
USER_ID = uuid4()
PORTFOLIO_RETRIEVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
SECURITY_RETRIEVED_AT = datetime(2026, 8, 31, 13, 0, tzinfo=UTC)


def portfolio_explanation() -> PortfolioExplanationContent:
    return PortfolioExplanationContent(
        summary="The portfolio is concentrated.",
        strengths=[],
        risks=[],
        concentration=[],
        performance=[],
        limitations=[],
    )


def security_explanation() -> SecurityExplanationContent:
    return SecurityExplanationContent(
        summary="The security has strong profitability.",
        valuation=[],
        growth_and_profitability=[],
        financial_health=[],
        performance=[],
        recent_developments=[],
        risks=[],
        limitations=[],
    )


@pytest.fixture
def llm_client() -> MagicMock:
    client = MagicMock()
    client.generate_structured = AsyncMock(return_value=portfolio_explanation())
    return client


@pytest.fixture
def service(llm_client: MagicMock) -> AIExplanationService:
    return AIExplanationService(
        llm_client=llm_client,
        portfolio_service=MagicMock(spec=PortfolioService),
        portfolio_analytics_service=MagicMock(spec=PortfolioAnalyticsService),
        research_service=MagicMock(spec=ResearchService),
        market_data_service=MagicMock(spec=MarketDataService),
    )


@pytest.fixture
def portfolio_context() -> SimpleNamespace:
    return SimpleNamespace(data_retrieved_at=PORTFOLIO_RETRIEVED_AT)


@pytest.fixture
def security_context() -> SimpleNamespace:
    return SimpleNamespace(symbol="AAPL", data_retrieved_at=SECURITY_RETRIEVED_AT)


@pytest.fixture
def portfolio_prompt() -> StructuredPrompt:
    return StructuredPrompt(
        system_prompt="Portfolio system prompt",
        user_prompt="Portfolio user prompt",
        output_type=PortfolioExplanationContent,
        schema_name=PORTFOLIO_SCHEMA_NAME,
    )


@pytest.fixture
def security_prompt() -> StructuredPrompt:
    return StructuredPrompt(
        system_prompt="Security system prompt",
        user_prompt="Security user prompt",
        output_type=SecurityExplanationContent,
        schema_name=SECURITY_SCHEMA_NAME,
    )


@pytest.fixture
def portfolio_builders(
    monkeypatch: pytest.MonkeyPatch,
    portfolio_context: SimpleNamespace,
    portfolio_prompt: StructuredPrompt,
) -> tuple[AsyncMock, MagicMock]:
    build_context = AsyncMock(return_value=portfolio_context)
    build_prompt = MagicMock(return_value=portfolio_prompt)
    monkeypatch.setattr(
        ai_explanation_service, "build_portfolio_ai_context", build_context
    )
    monkeypatch.setattr(
        ai_explanation_service, "build_portfolio_explanation_prompt", build_prompt
    )
    return build_context, build_prompt


@pytest.fixture
def security_builders(
    monkeypatch: pytest.MonkeyPatch,
    security_context: SimpleNamespace,
    security_prompt: StructuredPrompt,
) -> tuple[AsyncMock, MagicMock]:
    build_context = AsyncMock(return_value=security_context)
    build_prompt = MagicMock(return_value=security_prompt)
    monkeypatch.setattr(
        ai_explanation_service, "build_security_ai_context", build_context
    )
    monkeypatch.setattr(
        ai_explanation_service, "build_security_explanation_prompt", build_prompt
    )
    return build_context, build_prompt


@pytest.mark.asyncio
async def test_explain_portfolio_returns_portfolio_explanation_read(
    service: AIExplanationService,
    portfolio_builders: tuple[AsyncMock, MagicMock],
) -> None:
    result = await service.explain_portfolio(PORTFOLIO_ID, USER_ID)

    assert isinstance(result, PortfolioExplanationRead)
    assert result.explanation == portfolio_explanation()


@pytest.mark.asyncio
async def test_explain_portfolio_passes_prompt_data_to_llm_client(
    service: AIExplanationService,
    llm_client: MagicMock,
    portfolio_builders: tuple[AsyncMock, MagicMock],
    portfolio_prompt: StructuredPrompt,
) -> None:
    await service.explain_portfolio(PORTFOLIO_ID, USER_ID)

    llm_client.generate_structured.assert_awaited_once_with(
        system_prompt=portfolio_prompt.system_prompt,
        user_prompt=portfolio_prompt.user_prompt,
        output_type=PortfolioExplanationContent,
        schema_name=PORTFOLIO_SCHEMA_NAME,
    )


@pytest.mark.asyncio
async def test_explain_portfolio_preserves_identity_and_context_timestamp(
    service: AIExplanationService,
    portfolio_builders: tuple[AsyncMock, MagicMock],
) -> None:
    result = await service.explain_portfolio(PORTFOLIO_ID, USER_ID)

    assert result.portfolio_id == PORTFOLIO_ID
    assert result.data_retrieved_at == PORTFOLIO_RETRIEVED_AT


@pytest.mark.asyncio
async def test_explain_portfolio_sets_timezone_aware_generated_at(
    service: AIExplanationService,
    portfolio_builders: tuple[AsyncMock, MagicMock],
) -> None:
    result = await service.explain_portfolio(PORTFOLIO_ID, USER_ID)

    assert result.generated_at.tzinfo is not None
    assert result.generated_at.utcoffset() is not None


@pytest.mark.asyncio
async def test_explain_portfolio_propagates_portfolio_not_found(
    service: AIExplanationService,
    portfolio_builders: tuple[AsyncMock, MagicMock],
) -> None:
    build_context, _ = portfolio_builders
    build_context.side_effect = PortfolioNotFoundError("Portfolio not found")

    with pytest.raises(PortfolioNotFoundError):
        await service.explain_portfolio(PORTFOLIO_ID, USER_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        UpstreamTimeoutError("LLM timed out."),
        UpstreamUnavailableError("LLM unavailable."),
        UpstreamRateLimitedError("LLM rate limited."),
        UpstreamResponseError("LLM response invalid."),
    ],
)
async def test_explain_portfolio_propagates_upstream_llm_errors(
    service: AIExplanationService,
    llm_client: MagicMock,
    portfolio_builders: tuple[AsyncMock, MagicMock],
    error: Exception,
) -> None:
    llm_client.generate_structured.side_effect = error

    with pytest.raises(type(error)):
        await service.explain_portfolio(PORTFOLIO_ID, USER_ID)


@pytest.mark.asyncio
async def test_explain_security_returns_security_explanation_read(
    service: AIExplanationService,
    llm_client: MagicMock,
    security_builders: tuple[AsyncMock, MagicMock],
) -> None:
    llm_client.generate_structured.return_value = security_explanation()

    result = await service.explain_security("aapl")

    assert isinstance(result, SecurityExplanationRead)
    assert result.explanation == security_explanation()


@pytest.mark.asyncio
async def test_explain_security_passes_prompt_data_to_llm_client(
    service: AIExplanationService,
    llm_client: MagicMock,
    security_builders: tuple[AsyncMock, MagicMock],
    security_prompt: StructuredPrompt,
) -> None:
    llm_client.generate_structured.return_value = security_explanation()

    await service.explain_security("aapl")

    llm_client.generate_structured.assert_awaited_once_with(
        system_prompt=security_prompt.system_prompt,
        user_prompt=security_prompt.user_prompt,
        output_type=SecurityExplanationContent,
        schema_name=SECURITY_SCHEMA_NAME,
    )


@pytest.mark.asyncio
async def test_explain_security_uses_context_symbol_and_timestamp(
    service: AIExplanationService,
    llm_client: MagicMock,
    security_builders: tuple[AsyncMock, MagicMock],
) -> None:
    llm_client.generate_structured.return_value = security_explanation()

    result = await service.explain_security("aapl")

    assert result.symbol == "AAPL"
    assert result.data_retrieved_at == SECURITY_RETRIEVED_AT


@pytest.mark.asyncio
async def test_explain_security_sets_timezone_aware_generated_at(
    service: AIExplanationService,
    llm_client: MagicMock,
    security_builders: tuple[AsyncMock, MagicMock],
) -> None:
    llm_client.generate_structured.return_value = security_explanation()

    result = await service.explain_security("aapl")

    assert result.generated_at.tzinfo is not None
    assert result.generated_at.utcoffset() is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        UpstreamTimeoutError("LLM timed out."),
        UpstreamUnavailableError("LLM unavailable."),
        UpstreamRateLimitedError("LLM rate limited."),
        UpstreamResponseError("LLM response invalid."),
    ],
)
async def test_explain_security_propagates_upstream_llm_errors(
    service: AIExplanationService,
    llm_client: MagicMock,
    security_builders: tuple[AsyncMock, MagicMock],
    error: Exception,
) -> None:
    llm_client.generate_structured.side_effect = error

    with pytest.raises(type(error)):
        await service.explain_security("aapl")
