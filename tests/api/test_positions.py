from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from atlas_api.di import get_position_service
from atlas_api.schemas.position import PositionRead
from atlas_api.services.position_service import PositionService
from atlas_api.tools.errors import (
    PositionAlreadyExistsError,
    PositionNotFoundError,
    SecurityNotFoundError,
)
from atlas_api.tools.pagination import PaginatedResult, PaginationParams


def build_position_read(
    *,
    position_id: UUID | None = None,
    security_id: UUID | None = None,
    symbol: str = "AAPL",
    shares: Decimal | str = "10.50",
    average_cost: Decimal | str = "102.00",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> PositionRead:
    timestamp = datetime.now(UTC)
    return PositionRead(
        id=position_id or uuid4(),
        symbol=symbol,
        shares=Decimal(str(shares)),
        average_cost=Decimal(str(average_cost)),
        created_at=created_at or timestamp,
        updated_at=updated_at or timestamp,
    )


def position_read_json(position: PositionRead) -> dict[str, object]:
    return position.model_dump(mode="json")


def override_position_service(override_dependency):
    service = MagicMock(spec=PositionService)
    override_dependency(get_position_service, lambda: service)
    return service


def test_post_positions_returns_201_and_response_body_shape(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    created = build_position_read(
        position_id=uuid4(),
        symbol="AAPL",
        shares="25.50",
        average_cost="110.00",
    )
    service.create_position.return_value = created

    response = client.post(
        f"/portfolios/{portfolio_id}/positions",
        json={"symbol": " aapl ", "shares": "25.50", "average_cost": "110.00"},
    )

    assert response.status_code == 201
    assert response.json() == position_read_json(created)
    payload, called_portfolio_id, called_user_id = (
        service.create_position.call_args.args
    )
    assert payload.symbol == " aapl "
    assert payload.shares == Decimal("25.50")
    assert payload.average_cost == Decimal("110.00")
    assert called_portfolio_id == portfolio_id
    assert called_user_id == current_user_id


def test_get_positions_returns_200_and_list_shape(client, override_dependency) -> None:
    portfolio_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    first = build_position_read(
        position_id=uuid4(),
        symbol="AAPL",
        shares="8.00",
        average_cost="50.00",
    )
    second = build_position_read(
        position_id=uuid4(),
        symbol="MSFT",
        shares="12.00",
        average_cost="60.00",
    )
    service.get_all_positions.return_value = PaginatedResult(
        items=[first, second],
        total=2,
        page=1,
        page_size=25,
    )

    response = client.get(
        f"/portfolios/{portfolio_id}/positions", params={"page": 1, "page_size": 25}
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [position_read_json(first), position_read_json(second)],
        "total": 2,
        "page": 1,
        "page_size": 25,
    }
    service.get_all_positions.assert_called_once_with(
        portfolio_id,
        current_user_id,
        PaginationParams(page=1, page_size=25),
    )


def test_get_position_returns_200_for_found(client, override_dependency) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    position = build_position_read(
        position_id=position_id,
        symbol="AAPL",
        shares="14.00",
        average_cost="75.00",
    )
    service.get_position.return_value = position

    response = client.get(f"/portfolios/{portfolio_id}/positions/{position_id}")

    assert response.status_code == 200
    assert response.json() == position_read_json(position)
    service.get_position.assert_called_once_with(
        position_id, portfolio_id, current_user_id
    )


def test_get_position_returns_404_for_missing(client, override_dependency) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    service.get_position.side_effect = PositionNotFoundError("Position missing")

    response = client.get(f"/portfolios/{portfolio_id}/positions/{position_id}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "position_not_found",
            "message": "Position missing",
        }
    }
    service.get_position.assert_called_once_with(
        position_id, portfolio_id, current_user_id
    )


def test_patch_position_returns_200_and_updated_payload(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    updated = build_position_read(
        position_id=position_id,
        symbol="AAPL",
        shares="18.00",
        average_cost="85.00",
    )
    service.update_position.return_value = updated

    response = client.patch(
        f"/portfolios/{portfolio_id}/positions/{position_id}",
        json={"shares": "18.00", "average_cost": "85.00"},
    )

    assert response.status_code == 200
    assert response.json() == position_read_json(updated)
    called_position_id, called_portfolio_id, called_user_id, payload = (
        service.update_position.call_args.args
    )
    assert called_position_id == position_id
    assert called_portfolio_id == portfolio_id
    assert called_user_id == current_user_id
    assert payload.shares == Decimal("18.00")
    assert payload.average_cost == Decimal("85.00")


def test_delete_position_returns_204_with_no_body(client, override_dependency) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    service.delete_position.return_value = True

    response = client.delete(f"/portfolios/{portfolio_id}/positions/{position_id}")

    assert response.status_code == 204
    assert response.content == b""
    service.delete_position.assert_called_once_with(
        position_id, portfolio_id, current_user_id
    )


def test_post_positions_returns_404_for_missing_security(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    service = override_position_service(override_dependency)
    service.create_position.side_effect = SecurityNotFoundError("Security missing")

    response = client.post(
        f"/portfolios/{portfolio_id}/positions",
        json={"symbol": "AAPL", "shares": "5.00", "average_cost": "80.00"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "security_not_found",
            "message": "Security missing",
        }
    }


def test_get_position_returns_404_for_portfolio_ownership_mismatch(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    current_user_id = UUID("11111111-1111-1111-1111-111111111111")
    service = override_position_service(override_dependency)
    service.get_position.side_effect = PositionNotFoundError(
        "Position not found for this portfolio"
    )

    response = client.get(f"/portfolios/{portfolio_id}/positions/{position_id}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "position_not_found",
            "message": "Position not found for this portfolio",
        }
    }
    service.get_position.assert_called_once_with(
        position_id, portfolio_id, current_user_id
    )


def test_post_positions_returns_409_for_duplicate_position(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    service = override_position_service(override_dependency)
    service.create_position.side_effect = PositionAlreadyExistsError(
        "Duplicate position"
    )

    response = client.post(
        f"/portfolios/{portfolio_id}/positions",
        json={"symbol": "AAPL", "shares": "5.00", "average_cost": "80.00"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "position_already_exists",
            "message": "Duplicate position",
        }
    }


def test_patch_position_returns_422_for_invalid_shares_value(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    service = override_position_service(override_dependency)

    response = client.patch(
        f"/portfolios/{portfolio_id}/positions/{position_id}",
        json={"shares": "0"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "shares"]
    service.update_position.assert_not_called()


def test_patch_position_returns_422_for_invalid_average_cost_value(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    service = override_position_service(override_dependency)

    response = client.patch(
        f"/portfolios/{portfolio_id}/positions/{position_id}",
        json={"average_cost": "-1"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "average_cost"]
    service.update_position.assert_not_called()


def test_patch_position_returns_422_when_security_id_is_present(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    position_id = uuid4()
    service = override_position_service(override_dependency)

    response = client.patch(
        f"/portfolios/{portfolio_id}/positions/{position_id}",
        json={"security_id": str(uuid4())},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "security_id"]
    service.update_position.assert_not_called()


def test_post_positions_returns_422_for_schema_validation_failure(
    client, override_dependency
) -> None:
    portfolio_id = uuid4()
    service = override_position_service(override_dependency)

    response = client.post(
        f"/portfolios/{portfolio_id}/positions",
        json={"shares": "0", "average_cost": "1.00"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "symbol"]
    service.create_position.assert_not_called()
