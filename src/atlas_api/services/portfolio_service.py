import uuid
from datetime import UTC, datetime
from uuid import UUID

from atlas_api.models.portfolios import Portfolio
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate
from atlas_api.tools.errors import (
    InvalidPortfolioDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
)


class PortfolioService:
    def __init__(self, repository: PortfolioRepository):
        self.repository = repository
    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize the portfolio name for consistent storage and comparison."""
        return name.strip().casefold()

    def _to_read(self, model: Portfolio) -> PortfolioRead:
        return PortfolioRead.model_validate(model, from_attributes=True)
    
    def create_portfolio(self, payload: PortfolioCreate, user_id: UUID) -> PortfolioRead:
        """
        Creates a new portfolio.

        Args:
            payload (PortfolioCreate): The data for the new portfolio.
            user_id (UUID): The ID of the user creating the portfolio.

        Returns:
            PortfolioRead: The created portfolio with its details.
        """
        name = payload.name.strip()
        if not name:
            raise InvalidPortfolioDataError("Portfolio name must contain non-whitespace text.")
        normalized_name = self._normalize_name(name)
        for portfolio in (self._to_read(p) for p in self.repository.get_all_portfolios(user_id)):
            if self._normalize_name(portfolio.name) == normalized_name and portfolio.user_id == user_id:
                raise PortfolioAlreadyExistsError("Portfolio name already exists for this user.")
        portfolio_id = uuid.uuid4()
        portfolio = self.repository.create_portfolio(Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name=name,
            description=payload.description
        ))
        if not portfolio:
            raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")
        return self._to_read(portfolio)

    def get_all_portfolios(self, user_id: UUID) -> list[PortfolioRead]:
        """
        Retrieves all portfolios for a specific user.

        Args:
            user_id (UUID): The ID of the user whose portfolios are to be retrieved. """

        portfolios = [self._to_read(portfolio) for portfolio in self.repository.get_all_portfolios(user_id)]
        portfolios.sort(key=lambda p: p.created_at, reverse=True)
        return portfolios
    
    def get_portfolio(self, portfolio_id: UUID, user_id: UUID) -> PortfolioRead:
        """
        Retrieves a specific portfolio by its ID for a specific user.

        Args:
            portfolio_id (UUID): The ID of the portfolio to retrieve.
            user_id (UUID): The ID of the user who owns the portfolio."""
        portfolio = self.repository.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio:
            return self._to_read(portfolio)
        raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")
    
    def update_portfolio(self, portfolio_id: UUID, payload: PortfolioUpdate, user_id: UUID) -> PortfolioRead:
        """
        Updates a specific portfolio by its ID for a specific user.

        Args:
            portfolio_id (UUID): The ID of the portfolio to update.
            payload (PortfolioUpdate): The data to update the portfolio with.
            user_id (UUID): The ID of the user who owns the portfolio.

        Returns:
            PortfolioRead | None: The updated portfolio, or None if not found.
        """
        portfolio = self.repository.get_portfolio_by_id(portfolio_id, user_id)
        if not portfolio:
            raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")
        patch = payload.model_dump(exclude_unset=True)

        if "name" in patch:
            if patch["name"] is None:
                raise InvalidPortfolioDataError("Portfolio name cannot be set to None.")
            stripped = patch["name"].strip()
            if not stripped:
                raise InvalidPortfolioDataError("Portfolio name must contain non-whitespace text.")
            normalized_name = self._normalize_name(stripped)
            for portfolio in (self._to_read(p) for p in self.repository.get_all_portfolios(user_id)):
                if (
                    self._normalize_name(portfolio.name) == normalized_name
                    and portfolio.user_id == user_id
                    and portfolio.id != portfolio_id
                ):
                    raise PortfolioAlreadyExistsError("Portfolio name already exists for this user.")

        self.repository.update_portfolio(portfolio_id, payload, user_id)
        return self.get_portfolio(portfolio_id, user_id)
    
    def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> bool:
        """
        Deletes a specific portfolio by its ID.

        Args:
            portfolio_id (UUID): The ID of the portfolio to delete.
            user_id (UUID): The ID of the user who owns the portfolio.

        Returns:
            bool: True if the portfolio was deleted successfully, False if not found.
        """
        portfolio = self.repository.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio and portfolio.user_id == user_id:
            self.repository.delete_portfolio(portfolio_id, user_id)
            return True
        raise PortfolioNotFoundError(f"Portfolio with ID {portfolio_id} not found for user {user_id}")

    