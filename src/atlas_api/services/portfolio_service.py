from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlmodel import Session

from atlas_api.schemas.portfolio import PortfolioRead
from atlas_api.tools.errors import (
    InvalidPortfolioDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
)


class Store:
    """A simple in-memory store for portfolios."""
    _store: ClassVar[dict[UUID, PortfolioRead]] = {}

class PortfolioService:
    _store = Store._store

    def __init__(self, session: Session):
        # Initialize any required resources, such as database connections
        self.session = session

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize the portfolio name for consistent storage and comparison."""
        return name.strip().casefold()
    
    def create_portfolio(self, payload, user_id: UUID) -> PortfolioRead:
        """
        Creates a new portfolio.

        Args:
            payload (PortfolioCreate): The data for the new portfolio.
            user_id (UUID): The ID of the user creating the portfolio.

        Returns:
            PortfolioRead: The created portfolio with its details.
        """
        name = payload.name.strip()
        now = self._now_utc()
        if not name:
            raise InvalidPortfolioDataError("Portfolio name must contain non-whitespace text.")
        normalized_name = self._normalize_name(name)
        for portfolio in self._store.values():
            if self._normalize_name(portfolio.name) == normalized_name and portfolio.user_id == user_id:
                raise PortfolioAlreadyExistsError("Portfolio name already exists for this user.")
        
        created = PortfolioRead(
            id=uuid4(),
            user_id=user_id,
            name=name,
            description=payload.description,
            created_at=now,
            updated_at=now
        )
        self._store[created.id] = created
        return created

    def get_all_portfolios(self, user_id: UUID) -> list[PortfolioRead]:
        """
        Retrieves all portfolios for a specific user.

        Args:
            user_id (UUID): The ID of the user whose portfolios are to be retrieved. """

        portfolios = [portfolio for portfolio in self._store.values() if portfolio.user_id == user_id]
        portfolios.sort(key=lambda p: p.created_at, reverse=True)
        return portfolios
    
    def get_portfolio(self, portfolio_id: UUID, user_id: UUID) -> PortfolioRead:
        """
        Retrieves a specific portfolio by its ID for a specific user.

        Args:
            portfolio_id (UUID): The ID of the portfolio to retrieve.
            user_id (UUID): The ID of the user who owns the portfolio."""
        for portfolio in self._store.values():
            if portfolio.id == portfolio_id and portfolio.user_id == user_id:
                return portfolio
        raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")
    
    def update_portfolio(self, portfolio_id: UUID, payload, user_id: UUID) -> PortfolioRead:
        """
        Updates a specific portfolio by its ID for a specific user.

        Args:
            portfolio_id (UUID): The ID of the portfolio to update.
            payload (PortfolioUpdate): The data to update the portfolio with.
            user_id (UUID): The ID of the user who owns the portfolio.

        Returns:
            PortfolioRead | None: The updated portfolio, or None if not found.
        """
        existing = self.get_portfolio(portfolio_id, user_id)

        patch = payload.model_dump(exclude_unset=True)

        if "name" in patch:
            if patch["name"] is None:
                raise InvalidPortfolioDataError("Portfolio name cannot be set to None.")
            stripped = patch["name"].strip()
            if not stripped:
                raise InvalidPortfolioDataError("Portfolio name must contain non-whitespace text.")
            normalized_name = self._normalize_name(stripped)
            for portfolio in self._store.values():
                if (
                    self._normalize_name(portfolio.name) == normalized_name
                    and portfolio.user_id == user_id
                    and portfolio.id != portfolio_id
                ):
                    raise PortfolioAlreadyExistsError("Portfolio name already exists for this user.")
        updated = existing.model_copy(
            update = {
                **patch,
                "updated_at": self._now_utc(),
            }
        )
        self._store[updated.id] = updated
        return updated
    
    def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> bool:
        """
        Deletes a specific portfolio by its ID.

        Args:
            portfolio_id (UUID): The ID of the portfolio to delete.
            user_id (UUID): The ID of the user who owns the portfolio.

        Returns:
            bool: True if the portfolio was deleted successfully, False if not found.
        """
        portfolio = self._store.get(portfolio_id)
        if portfolio and portfolio.user_id == user_id:
            del self._store[portfolio_id]
            return True
        raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")

    