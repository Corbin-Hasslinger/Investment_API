from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from atlas_api.models.portfolios import Portfolio
from atlas_api.models.users import User
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.schemas.portfolio import PortfolioUpdate


def test_create_and_fetch_by_id_and_user_id(session, user) -> None:
    repository = PortfolioRepository(session)
    portfolio = Portfolio(
        user_id=user.id,
        name="Long Term",
        description="Retirement holdings",
    )

    created = repository.create_portfolio(portfolio)
    fetched = repository.get_portfolio_by_id(created.id, user.id)

    assert created.id is not None
    assert created.user_id == user.id
    assert created.name == "Long Term"
    assert created.description == "Retirement holdings"
    assert created.created_at is not None
    assert created.updated_at is not None
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.user_id == user.id
    assert fetched.name == "Long Term"
    assert fetched.description == "Retirement holdings"


def test_get_by_id_returns_none_for_wrong_user_id(session, user) -> None:
    repository = PortfolioRepository(session)
    portfolio = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Growth", description="Growth picks")
    )

    assert repository.get_portfolio_by_id(portfolio.id, uuid4()) is None


def test_list_returns_only_that_users_portfolios(session, user) -> None:
    repository = PortfolioRepository(session)
    other_user = User(email=f"other-{uuid4()}@example.com", hashed_password="hashed-password")
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    first = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Income", description="Dividends")
    )
    second = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Speculative", description="High risk")
    )
    repository.create_portfolio(
        Portfolio(user_id=other_user.id, name="Other User", description="Ignore me")
    )

    portfolios = repository.get_all_portfolios(user.id)

    assert {portfolio.id for portfolio in portfolios} == {first.id, second.id}
    assert all(portfolio.user_id == user.id for portfolio in portfolios)


def test_update_persists_changed_name_and_description(session, user) -> None:
    repository = PortfolioRepository(session)
    portfolio = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Core", description="Initial description")
    )
    original_created_at = portfolio.created_at
    original_updated_at = portfolio.updated_at

    repository.update_portfolio(
        portfolio.id,
        PortfolioUpdate(name="Core Updated", description="Updated description"),
        user.id,
    )
    updated = repository.get_portfolio_by_id(portfolio.id, user.id)

    assert updated is not None
    assert updated.name == "Core Updated"
    assert updated.description == "Updated description"
    assert updated.created_at == original_created_at
    assert updated.updated_at is not None
    assert updated.updated_at >= original_updated_at


def test_delete_removes_row(session, user) -> None:
    repository = PortfolioRepository(session)
    portfolio = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Delete Me", description="Disposable")
    )

    repository.delete_portfolio(portfolio.id, user.id)

    assert repository.get_portfolio_by_id(portfolio.id, user.id) is None


def test_same_user_duplicate_name_is_rejected(session, user) -> None:
    repository = PortfolioRepository(session)
    repository.create_portfolio(
        Portfolio(user_id=user.id, name="Duplicate", description="First")
    )

    try:
        repository.create_portfolio(
            Portfolio(user_id=user.id, name="Duplicate", description="Second")
        )
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Expected same-user duplicate portfolio name to violate uniqueness.")


def test_different_users_can_share_the_same_name(session, user) -> None:
    repository = PortfolioRepository(session)
    other_user = User(email=f"another-{uuid4()}@example.com", hashed_password="hashed-password")
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    first = repository.create_portfolio(
        Portfolio(user_id=user.id, name="Shared Name", description="First owner")
    )
    second = repository.create_portfolio(
        Portfolio(user_id=other_user.id, name="Shared Name", description="Second owner")
    )

    assert first.id != second.id
    assert first.user_id == user.id
    assert second.user_id == other_user.id