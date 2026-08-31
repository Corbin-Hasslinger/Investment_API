from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from atlas_api.di import get_ai_explanation_service
from atlas_api.schemas.ai import (
    PortfolioExplanationContent,
    PortfolioExplanationRead,
    SecurityExplanationContent,
    SecurityExplanationRead,
)
from atlas_api.services.ai_explanation_service import AIExplanationService
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

# Matches the dev-only current user id returned by di.get_current_user.
CURRENT_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
PORTFOLIO_ID = uuid4()
DATA_RETRIEVED_AT = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 8, 31, 12, 0, 5, tzinfo=UTC)


def build_portfolio_explanation_read() -> PortfolioExplanationRead:
    return PortfolioExplanationRead(
        portfolio_id=PORTFOLIO_ID,
        data_retrieved_at=DATA_RETRIEVED_AT,
        generated_at=GENERATED_AT,
        explanation=PortfolioExplanationContent(
            summary="The portfolio is concentrated in technology.",
            strengths=[],
            risks=[],
            concentration=[],
            performance=[],
            limitations=[],
        ),
    )


def build_security_explanation_read() -> SecurityExplanationRead:
    return SecurityExplanationRead(
        symbol="AAPL",
        data_retrieved_at=DATA_RETRIEVED_AT,
        generated_at=GENERATED_AT,
        explanation=SecurityExplanationContent(
            summary="The security has strong profitability.",
            valuation=[],
            growth_and_profitability=[],
            financial_health=[],
            performance=[],
            recent_developments=[],
            risks=[],
            limitations=[],
        ),
    )


def override_ai_explanation_service(override_dependency) -> MagicMock:
    service = MagicMock(spec=AIExplanationService)
    service.explain_portfolio = AsyncMock()
    service.explain_security = AsyncMock()
    override_dependency(get_ai_explanation_service, lambda: service)
    return service


def test_get_portfolio_explanation_returns_200(client, override_dependency) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_portfolio.return_value = build_portfolio_explanation_read()

    response = client.get(f"/explanations/portfolios/{PORTFOLIO_ID}")

    assert response.status_code == 200


def test_get_portfolio_explanation_returns_expected_shape(
    client, override_dependency
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_portfolio.return_value = build_portfolio_explanation_read()

    response = client.get(f"/explanations/portfolios/{PORTFOLIO_ID}")

    body = response.json()
    assert body["portfolio_id"] == str(PORTFOLIO_ID)
    assert body["data_retrieved_at"] == "2026-08-31T12:00:00Z"
    assert body["generated_at"] == "2026-08-31T12:00:05Z"
    assert (
        body["explanation"]["summary"] == "The portfolio is concentrated in technology."
    )
    assert body["explanation"]["strengths"] == []
    assert body["explanation"]["risks"] == []
    assert body["explanation"]["concentration"] == []
    assert body["explanation"]["performance"] == []
    assert body["explanation"]["limitations"] == []


def test_get_portfolio_explanation_passes_portfolio_id_and_current_user(
    client, override_dependency
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_portfolio.return_value = build_portfolio_explanation_read()

    client.get(f"/explanations/portfolios/{PORTFOLIO_ID}")

    service.explain_portfolio.assert_awaited_once_with(
        portfolio_id=PORTFOLIO_ID, user_id=CURRENT_USER_ID
    )


def test_get_portfolio_explanation_returns_404_for_portfolio_not_found(
    client, override_dependency
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_portfolio.side_effect = PortfolioNotFoundError(
        "Portfolio not found"
    )

    response = client.get(f"/explanations/portfolios/{PORTFOLIO_ID}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "portfolio_not_found"


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (UpstreamTimeoutError("LLM timed out."), 504, "upstream_timeout"),
        (UpstreamRateLimitedError("LLM rate limited."), 429, "upstream_rate_limited"),
        (UpstreamUnavailableError("LLM unavailable."), 503, "upstream_unavailable"),
        (
            UpstreamResponseError("LLM response invalid."),
            502,
            "upstream_response_error",
        ),
    ],
)
def test_get_portfolio_explanation_maps_upstream_errors(
    client,
    override_dependency,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_portfolio.side_effect = error

    response = client.get(f"/explanations/portfolios/{PORTFOLIO_ID}")

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code


def test_get_security_explanation_returns_200(client, override_dependency) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_security.return_value = build_security_explanation_read()

    response = client.get("/explanations/securities/aapl")

    assert response.status_code == 200


def test_get_security_explanation_returns_expected_shape(
    client, override_dependency
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_security.return_value = build_security_explanation_read()

    response = client.get("/explanations/securities/aapl")

    body = response.json()
    assert body["symbol"] == "AAPL"
    assert body["data_retrieved_at"] == "2026-08-31T12:00:00Z"
    assert body["generated_at"] == "2026-08-31T12:00:05Z"
    assert body["explanation"]["summary"] == "The security has strong profitability."
    assert body["explanation"]["valuation"] == []
    assert body["explanation"]["growth_and_profitability"] == []
    assert body["explanation"]["financial_health"] == []
    assert body["explanation"]["performance"] == []
    assert body["explanation"]["recent_developments"] == []
    assert body["explanation"]["risks"] == []
    assert body["explanation"]["limitations"] == []


def test_get_security_explanation_forwards_supplied_symbol(
    client, override_dependency
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_security.return_value = build_security_explanation_read()

    client.get("/explanations/securities/aapl")

    service.explain_security.assert_awaited_once_with(symbol="aapl")


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (UpstreamTimeoutError("LLM timed out."), 504, "upstream_timeout"),
        (UpstreamRateLimitedError("LLM rate limited."), 429, "upstream_rate_limited"),
        (UpstreamUnavailableError("LLM unavailable."), 503, "upstream_unavailable"),
        (
            UpstreamResponseError("LLM response invalid."),
            502,
            "upstream_response_error",
        ),
    ],
)
def test_get_security_explanation_maps_upstream_errors(
    client,
    override_dependency,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = override_ai_explanation_service(override_dependency)
    service.explain_security.side_effect = error

    response = client.get("/explanations/securities/aapl")

    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
