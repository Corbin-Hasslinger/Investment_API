from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from atlas_api.models.portfolios import Portfolio
from atlas_api.models.positions import Position
from atlas_api.models.securities import Security
from atlas_api.models.users import User
from atlas_api.repositories.position_repository import PositionRepository
from atlas_api.schemas.position import PositionUpdate


def make_security(symbol: str) -> Security:
    return Security(
        symbol=symbol,
        name=f"{symbol} Corp",
        exchange="NASDAQ",
        currency="USD",
    )


def test_create_and_fetch_by_id_and_portfolio_id(session, portfolio, security) -> None:
    repository = PositionRepository(session)
    position = repository.create_position(
        Position(
            portfolio_id=portfolio.id,
            security_id=security.id,
            shares=Decimal("12.50"),
            average_cost=Decimal("101.25"),
        )
    )

    fetched = repository.get_position_by_id(position.id, portfolio.id)

    assert position.id is not None
    assert position.portfolio_id == portfolio.id
    assert position.security_id == security.id
    assert position.shares == Decimal("12.50")
    assert position.average_cost == Decimal("101.25")
    assert fetched is not None
    assert fetched.id == position.id
    assert fetched.portfolio_id == portfolio.id
    assert fetched.security_id == security.id


def test_get_by_id_returns_none_for_wrong_portfolio_id(session, portfolio, security) -> None:
    repository = PositionRepository(session)
    position = repository.create_position(
        Position(
            portfolio_id=portfolio.id,
            security_id=security.id,
            shares=Decimal("5.00"),
            average_cost=Decimal("90.00"),
        )
    )

    assert repository.get_position_by_id(position.id, uuid4()) is None


def test_list_returns_only_positions_for_selected_portfolio(session, user, security) -> None:
    repository = PositionRepository(session)
    other_user = User(email=f"other-{uuid4()}@example.com", hashed_password="hashed-password")
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    other_portfolio = Portfolio(user_id=other_user.id, name="Portfolio B", description="Beta")
    target_portfolio = Portfolio(user_id=user.id, name="Portfolio C", description="Gamma")
    session.add_all([other_portfolio, target_portfolio])
    session.commit()
    session.refresh(other_portfolio)
    session.refresh(target_portfolio)

    repository.create_position(
        Position(
            portfolio_id=other_portfolio.id,
            security_id=security.id,
            shares=Decimal("30.00"),
            average_cost=Decimal("120.00"),
        )
    )
    position_in_target = repository.create_position(
        Position(
            portfolio_id=target_portfolio.id,
            security_id=security.id,
            shares=Decimal("20.00"),
            average_cost=Decimal("110.00"),
        )
    )

    positions = repository.get_all_positions(target_portfolio.id)

    assert [position.id for position in positions] == [position_in_target.id]
    assert all(position.portfolio_id == target_portfolio.id for position in positions)


def test_update_persists_changed_shares_and_average_cost(session, portfolio, security) -> None:
    repository = PositionRepository(session)
    position = repository.create_position(
        Position(
            portfolio_id=portfolio.id,
            security_id=security.id,
            shares=Decimal("8.00"),
            average_cost=Decimal("50.00"),
        )
    )
    original_created_at = position.created_at
    original_updated_at = position.updated_at

    repository.update_position(
        position.id,
        portfolio.id,
        PositionUpdate(shares=Decimal("12.25"), average_cost=Decimal("60.00")),
    )
    updated = repository.get_position_by_id(position.id, portfolio.id)

    assert updated is not None
    assert updated.shares == Decimal("12.25")
    assert updated.average_cost == Decimal("60.00")
    assert updated.created_at == original_created_at
    assert updated.updated_at is not None
    assert updated.updated_at >= original_updated_at


def test_delete_removes_row(session, portfolio, security) -> None:
    repository = PositionRepository(session)
    position = repository.create_position(
        Position(
            portfolio_id=portfolio.id,
            security_id=security.id,
            shares=Decimal("9.00"),
            average_cost=Decimal("80.00"),
        )
    )

    repository.delete_position(position.id, portfolio.id)

    assert repository.get_position_by_id(position.id, portfolio.id) is None


def test_same_portfolio_and_security_duplicate_is_rejected(session, portfolio, security) -> None:
    repository = PositionRepository(session)
    repository.create_position(
        Position(
            portfolio_id=portfolio.id,
            security_id=security.id,
            shares=Decimal("3.00"),
            average_cost=Decimal("30.00"),
        )
    )

    try:
        repository.create_position(
            Position(
                portfolio_id=portfolio.id,
                security_id=security.id,
                shares=Decimal("4.00"),
                average_cost=Decimal("40.00"),
            )
        )
        session.flush()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Expected same portfolio/security duplicate to violate uniqueness.")


def test_different_portfolios_can_share_the_same_security(session, user) -> None:
    repository = PositionRepository(session)
    aapl = make_security("AAPL")
    session.add(aapl)
    session.commit()
    session.refresh(aapl)

    first_portfolio = Portfolio(user_id=user.id, name="First Portfolio", description="Alpha")
    second_portfolio = Portfolio(user_id=user.id, name="Second Portfolio", description="Beta")
    session.add_all([first_portfolio, second_portfolio])
    session.commit()
    session.refresh(first_portfolio)
    session.refresh(second_portfolio)

    first = repository.create_position(
        Position(
            portfolio_id=first_portfolio.id,
            security_id=aapl.id,
            shares=Decimal("10.00"),
            average_cost=Decimal("150.00"),
        )
    )
    second = repository.create_position(
        Position(
            portfolio_id=second_portfolio.id,
            security_id=aapl.id,
            shares=Decimal("7.00"),
            average_cost=Decimal("155.00"),
        )
    )

    assert first.id != second.id
    assert first.security_id == second.security_id
    assert first.portfolio_id != second.portfolio_id
