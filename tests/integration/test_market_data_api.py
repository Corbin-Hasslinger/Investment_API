from unittest.mock import AsyncMock, MagicMock

from sqlmodel import select

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.core.db import get_session
from atlas_api.di import get_current_user, get_finnhub_client
from atlas_api.models.positions import Position
from atlas_api.models.securities import Security
from atlas_api.schemas.user import CurrentUserRead


def test_get_quote_uses_real_security_repository_and_mocked_finnhub(
    client,
    override_dependency,
    session,
    security,
) -> None:
    """The quote route composes real DB-backed services with a mocked upstream."""
    finnhub_client = MagicMock(spec=FinnhubClient)
    finnhub_client.get_quote = AsyncMock(
        return_value={
            "c": 150.25,
            "d": 2.50,
            "dp": 1.69,
            "h": 152.00,
            "l": 149.50,
            "o": 149.00,
            "pc": 147.75,
            "t": 1692374400,
        }
    )

    def override_session():
        yield session

    override_dependency(get_session, override_session)
    override_dependency(get_finnhub_client, lambda: finnhub_client)

    response = client.get("/market/quote/aapl")

    assert response.status_code == 200
    assert response.json() == {
        "symbol": security.symbol,
        "current_price": "150.25",
        "price_change": "2.5",
        "percent_change": "1.69",
        "high_price": "152.0",
        "low_price": "149.5",
        "open_price": "149.0",
        "previous_close_price": "147.75",
        "timestamp": 1692374400,
    }
    finnhub_client.get_quote.assert_awaited_once_with("AAPL")


def test_post_position_resolves_security_and_persists_position(
    client,
    override_dependency,
    session,
    user,
    portfolio,
) -> None:
    """POST positions composes ownership, security resolution, and persistence."""
    finnhub_client = MagicMock(spec=FinnhubClient)
    finnhub_client.symbol_lookup = AsyncMock(
        return_value={
            "name": "Apple Inc.",
            "exchange": "NASDAQ",
            "currency": "USD",
        }
    )

    def override_session():
        yield session

    override_dependency(get_session, override_session)
    override_dependency(get_finnhub_client, lambda: finnhub_client)
    override_dependency(
        get_current_user,
        lambda: CurrentUserRead(id=user.id, email=user.email),
    )

    response = client.post(
        f"/portfolios/{portfolio.id}/positions",
        json={"symbol": "aapl", "shares": "10.5", "average_cost": "150.25"},
    )

    assert response.status_code == 201
    assert response.json()["symbol"] == "AAPL"
    assert response.json()["shares"] == "10.500000"
    assert response.json()["average_cost"] == "150.250000"

    created_security = session.exec(
        select(Security).where(Security.symbol == "AAPL")
    ).first()
    created_position = session.exec(
        select(Position).where(
            Position.portfolio_id == portfolio.id,
            Position.symbol == "AAPL",
        )
    ).first()

    assert created_security is not None
    assert created_position is not None
    assert created_security.name == "Apple Inc."
    assert created_security.exchange == "NASDAQ"
    assert created_security.currency == "USD"
    assert created_position.shares == 10.5
    assert created_position.average_cost == 150.25
    finnhub_client.symbol_lookup.assert_awaited_once_with("AAPL")
