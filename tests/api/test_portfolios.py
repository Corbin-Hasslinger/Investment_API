from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from atlas_api.di import get_current_user, get_portfolio_service
from atlas_api.schemas.portfolio import PortfolioRead
from atlas_api.schemas.user import CurrentUserRead
from atlas_api.services.portfolio_service import PortfolioService
from atlas_api.tools.errors import PortfolioAlreadyExistsError, PortfolioNotFoundError
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