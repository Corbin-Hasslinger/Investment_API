from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from atlas_api.di import (
    get_current_user,
    get_portfolio_analytics_service,
    get_portfolio_service,
)
from atlas_api.schemas.analytics import (
    PortfolioAnalyticsRead,
    PortfolioPositionAnalyticsRead,
)
from atlas_api.schemas.portfolio import PortfolioRead
from atlas_api.schemas.user import CurrentUserRead
from atlas_api.services.portfolio_analytics_service import PortfolioAnalyticsService
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.tools.errors import (
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)
from atlas_api.tools.pagination import PaginatedResult, PaginationParams


def build_portfolio_read(
    *,
    portfolio_id: UUID | None = None,
    user_id: UUID | None = None,
    name: str = "Core Holdings",
    description: str | None = "Long-term positions",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PortfolioRead:
    timestamp = datetime.now(UTC)
    return PortfolioRead(
        id=portfolio_id or uuid4(),
        user_id=user_id or uuid4(),
        name=name,
        description=description,
        created_at=created_at or timestamp,
        updated_at=updated_at or timestamp,
    )


def portfolio_read_json(portfolio: PortfolioRead) -> dict[str, object]:
    return portfolio.model_dump(mode="json")


def override_current_user(override_dependency, user_id: UUID) -> CurrentUserRead:
    current_user = CurrentUserRead(id=user_id, email="portfolio-user@atlas.local")
    override_dependency(get_current_user, lambda: current_user)
    return current_user


def override_portfolio_service(override_dependency) -> MagicMock:
    service = MagicMock(spec=PortfolioService)
    override_dependency(get_portfolio_service, lambda: service)
    return service


def override_portfolio_analytics_service(override_dependency) -> MagicMock:
    service = MagicMock(spec=PortfolioAnalyticsService)
    override_dependency(get_portfolio_analytics_service, lambda: service)
    return service


def build_portfolio_analytics_read(
    *,
    portfolio_id: UUID,
    positions: list[PortfolioPositionAnalyticsRead] | None = None,
) -> PortfolioAnalyticsRead:
    analytics_positions = positions or []
    total_market_value = sum(
        (position.market_value for position in analytics_positions), Decimal("0.00")
    )
    total_cost_basis = sum(
        (position.cost_basis for position in analytics_positions), Decimal("0.00")
    )
    total_unrealized_gain_loss = sum(
        (position.unrealized_gain_loss for position in analytics_positions),
        Decimal("0.00"),
    )
    return PortfolioAnalyticsRead(
        portfolio_id=portfolio_id,
        total_market_value=total_market_value,
        total_cost_basis=total_cost_basis,
        total_unrealized_gain_loss=total_unrealized_gain_loss,
        total_unrealized_gain_loss_percent=Decimal("25.00") if total_cost_basis else None,
        positions=analytics_positions,
    )


def build_position_analytics_read() -> PortfolioPositionAnalyticsRead:
    return PortfolioPositionAnalyticsRead(
        symbol="AAPL",
        shares=Decimal("10"),
        average_cost=Decimal("100.00"),
        current_price=Decimal("125.00"),
        market_value=Decimal("1250.00"),
        cost_basis=Decimal("1000.00"),
        unrealized_gain_loss=Decimal("250.00"),
        unrealized_gain_loss_percent=Decimal("25.00"),
        allocation_percent=Decimal("100.00"),
    )


def test_post_portfolios_returns_201_and_response_body_shape(client, override_dependency) -> None:
    user_id = UUID("33333333-3333-3333-3333-333333333333")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    created = build_portfolio_read(user_id=current_user.id, name="Growth", description="Aggressive picks")
    service.create_portfolio.return_value = created

    response = client.post(
        "/portfolios",
        json={"name": "Growth", "description": "Aggressive picks"},
    )

    assert response.status_code == 201
    assert response.json() == portfolio_read_json(created)
    payload, called_user_id = service.create_portfolio.call_args.args
    assert payload.name == "Growth"
    assert payload.description == "Aggressive picks"
    assert called_user_id == current_user.id


def test_get_portfolios_returns_200_and_list_shape(client, override_dependency) -> None:
    user_id = UUID("44444444-4444-4444-4444-444444444444")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    first = build_portfolio_read(user_id=current_user.id, name="Income", description="Dividend stocks")
    second = build_portfolio_read(user_id=current_user.id, name="Value", description=None)
    service.get_all_portfolios.return_value = PaginatedResult(
        items=[first, second],
        total=2,
        page=1,
        page_size=25,
    )

    response = client.get("/portfolios")

    assert response.status_code == 200
    assert response.json() == {
        "items": [portfolio_read_json(first), portfolio_read_json(second)],
        "total": 2,
        "page": 1,
        "page_size": 25,
    }
    service.get_all_portfolios.assert_called_once()
    called_user_id, called_pagination = service.get_all_portfolios.call_args.args
    assert called_user_id == current_user.id
    assert called_pagination == PaginationParams(page=1, page_size=25)


def test_get_portfolio_returns_200_for_found(client, override_dependency) -> None:
    user_id = UUID("55555555-5555-5555-5555-555555555555")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    portfolio = build_portfolio_read(user_id=current_user.id, name="Core", description="Main account")
    service.get_portfolio.return_value = portfolio

    response = client.get(f"/portfolios/{portfolio.id}")

    assert response.status_code == 200
    assert response.json() == portfolio_read_json(portfolio)
    service.get_portfolio.assert_called_once_with(portfolio.id, current_user.id)


def test_get_portfolio_returns_404_for_missing(client, override_dependency) -> None:
    user_id = UUID("66666666-6666-6666-6666-666666666666")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    portfolio_id = uuid4()
    service.get_portfolio.side_effect = PortfolioNotFoundError("Portfolio missing")

    response = client.get(f"/portfolios/{portfolio_id}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "portfolio_not_found",
            "message": "Portfolio missing",
        }
    }
    service.get_portfolio.assert_called_once_with(portfolio_id, current_user.id)


def test_patch_portfolio_returns_200_and_updated_payload(client, override_dependency) -> None:
    user_id = UUID("77777777-7777-7777-7777-777777777777")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    portfolio_id = uuid4()
    updated = build_portfolio_read(user_id=current_user.id, portfolio_id=portfolio_id, name="Updated", description="Adjusted")
    service.update_portfolio.return_value = updated

    response = client.patch(
        f"/portfolios/{portfolio_id}",
        json={"name": "Updated", "description": "Adjusted"},
    )

    assert response.status_code == 200
    assert response.json() == portfolio_read_json(updated)
    called_portfolio_id, payload, called_user_id = service.update_portfolio.call_args.args
    assert called_portfolio_id == portfolio_id
    assert payload.name == "Updated"
    assert payload.description == "Adjusted"
    assert called_user_id == current_user.id


def test_delete_portfolio_returns_204_with_no_body(client, override_dependency) -> None:
    user_id = UUID("88888888-8888-8888-8888-888888888888")
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    portfolio_id = uuid4()
    service.delete_portfolio.return_value = True

    response = client.delete(f"/portfolios/{portfolio_id}")

    assert response.status_code == 204
    assert response.content == b""
    service.delete_portfolio.assert_called_once_with(portfolio_id, current_user.id)


def test_post_portfolios_returns_409_for_duplicate_name(client, override_dependency) -> None:
    user_id = UUID("99999999-9999-9999-9999-999999999999")
    override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    service.create_portfolio.side_effect = PortfolioAlreadyExistsError("Duplicate portfolio name")

    response = client.post(
        "/portfolios",
        json={"name": "Growth", "description": "Duplicate"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "portfolio_already_exists",
            "message": "Duplicate portfolio name",
        }
    }


def test_post_portfolios_returns_422_for_schema_validation_failure(client, override_dependency) -> None:
    override_current_user(override_dependency, UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    service = override_portfolio_service(override_dependency)

    response = client.post(
        "/portfolios",
        json={"description": "Missing required name"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "name"]
    service.create_portfolio.assert_not_called()


def test_patch_portfolios_returns_422_for_schema_validation_failure(client, override_dependency) -> None:
    override_current_user(override_dependency, UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    service = override_portfolio_service(override_dependency)

    response = client.patch(
        f"/portfolios/{uuid4()}",
        json={"name": 123},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "name"]
    service.update_portfolio.assert_not_called()


def test_get_portfolio_analytics_returns_200_with_analytics_response(client, override_dependency) -> None:
    user_id = uuid4()
    portfolio_id = uuid4()
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_analytics_service(override_dependency)
    analytics = build_portfolio_analytics_read(
        portfolio_id=portfolio_id,
        positions=[build_position_analytics_read()],
    )
    service.get_portfolio_analytics.return_value = analytics

    response = client.get(f"/portfolios/{portfolio_id}/analytics")

    assert response.status_code == 200
    assert response.json() == analytics.model_dump(mode="json")
    service.get_portfolio_analytics.assert_awaited_once_with(portfolio_id, current_user.id)


def test_get_portfolio_analytics_returns_200_for_empty_portfolio(client, override_dependency) -> None:
    user_id = uuid4()
    portfolio_id = uuid4()
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_analytics_service(override_dependency)
    analytics = build_portfolio_analytics_read(portfolio_id=portfolio_id)
    service.get_portfolio_analytics.return_value = analytics

    response = client.get(f"/portfolios/{portfolio_id}/analytics")

    assert response.status_code == 200
    assert response.json() == {
        "portfolio_id": str(portfolio_id),
        "total_market_value": "0.00",
        "total_cost_basis": "0.00",
        "total_unrealized_gain_loss": "0.00",
        "total_unrealized_gain_loss_percent": None,
        "positions": [],
    }
    service.get_portfolio_analytics.assert_awaited_once_with(portfolio_id, current_user.id)


def test_get_portfolio_analytics_returns_404_for_missing_portfolio(client, override_dependency) -> None:
    user_id = uuid4()
    portfolio_id = uuid4()
    override_current_user(override_dependency, user_id)
    service = override_portfolio_analytics_service(override_dependency)
    service.get_portfolio_analytics.side_effect = PortfolioNotFoundError("Portfolio missing")

    response = client.get(f"/portfolios/{portfolio_id}/analytics")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "portfolio_not_found", "message": "Portfolio missing"}
    }
    service.get_portfolio_analytics.assert_awaited_once_with(portfolio_id, user_id)


@pytest.mark.parametrize(
    ("error", "status_code", "error_code"),
    [
        (UpstreamTimeoutError("Finnhub timed out"), 504, "upstream_timeout"),
        (UpstreamRateLimitedError("Finnhub rate limited"), 429, "upstream_rate_limited"),
        (UpstreamUnavailableError("Finnhub unavailable"), 503, "upstream_unavailable"),
    ],
)
def test_get_portfolio_analytics_maps_upstream_errors(
    client,
    override_dependency,
    error,
    status_code,
    error_code,
) -> None:
    user_id = uuid4()
    portfolio_id = uuid4()
    override_current_user(override_dependency, user_id)
    service = override_portfolio_analytics_service(override_dependency)
    service.get_portfolio_analytics.side_effect = error

    response = client.get(f"/portfolios/{portfolio_id}/analytics")

    assert response.status_code == status_code
    assert response.json() == {
        "error": {"code": error_code, "message": str(error)}
    }
    service.get_portfolio_analytics.assert_awaited_once_with(portfolio_id, user_id)


def test_get_portfolio_analytics_returns_422_for_invalid_portfolio_id(client, override_dependency) -> None:
    override_current_user(override_dependency, uuid4())
    service = override_portfolio_analytics_service(override_dependency)

    response = client.get("/portfolios/not-a-uuid/analytics")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "portfolio_id"]
    service.get_portfolio_analytics.assert_not_called()


def test_get_portfolio_detail_route_still_works_with_analytics_route(client, override_dependency) -> None:
    user_id = uuid4()
    portfolio_id = uuid4()
    current_user = override_current_user(override_dependency, user_id)
    service = override_portfolio_service(override_dependency)
    portfolio = build_portfolio_read(
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        name="Core Holdings",
    )
    service.get_portfolio.return_value = portfolio

    response = client.get(f"/portfolios/{portfolio_id}")

    assert response.status_code == 200
    assert response.json() == portfolio_read_json(portfolio)
    service.get_portfolio.assert_called_once_with(portfolio_id, current_user.id)