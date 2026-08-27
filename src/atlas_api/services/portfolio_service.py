import uuid
from uuid import UUID

from atlas_api.models.portfolios import Portfolio
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate
from atlas_api.tools.errors import (
    InvalidPortfolioDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
)
from atlas_api.tools.pagination import PaginatedResult, PaginationParams


class PortfolioService:
    def __init__(self, repository: PortfolioRepository):
        self.repository = repository

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize the portfolio name for consistent storage and comparison."""
        return name.strip().casefold()

    def _to_read(self, model: Portfolio) -> PortfolioRead:
        return PortfolioRead.model_validate(model, from_attributes=True)

    def create_portfolio(
        self, payload: PortfolioCreate, user_id: UUID
    ) -> PortfolioRead:
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
            raise InvalidPortfolioDataError(
                "Portfolio name must contain non-whitespace text."
            )
        normalized_name = self._normalize_name(name)
        if self.repository.exists_by_name(normalized_name, user_id):
            raise PortfolioAlreadyExistsError(
                "Portfolio name already exists for this user."
            )
        portfolio_id = uuid.uuid4()
        portfolio = self.repository.create_portfolio(
            Portfolio(
                id=portfolio_id,
                user_id=user_id,
                name=name,
                description=payload.description,
            )
        )
        self.repository.commit()
        self.repository.refresh(portfolio)
        return self._to_read(portfolio)

    def get_all_portfolios(
        self, user_id: UUID, pagination: PaginationParams
    ) -> PaginatedResult[PortfolioRead]:
        """
        Retrieves all portfolios for a specific user.

        Args:
            user_id (UUID): The ID of the user whose portfolios are to be retrieved."""

        portfolios = [
            self._to_read(portfolio)
            for portfolio in self.repository.get_all_portfolios(user_id)
        ]
        total = len(portfolios)
        start = (pagination.page - 1) * pagination.page_size
        end = start + pagination.page_size
        page_items = portfolios[start:end]
        return PaginatedResult(
            items=page_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_portfolio(self, portfolio_id: UUID, user_id: UUID) -> PortfolioRead:
        """
        Retrieves a specific portfolio by its ID for a specific user.

        Args:
            portfolio_id (UUID): The ID of the portfolio to retrieve.
            user_id (UUID): The ID of the user who owns the portfolio."""
        portfolio = self.repository.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio:
            return self._to_read(portfolio)
        raise PortfolioNotFoundError(
            f"Portfolio with ID {portfolio_id} not found for user {user_id}"
        )

    def update_portfolio(
        self, portfolio_id: UUID, payload: PortfolioUpdate, user_id: UUID
    ) -> PortfolioRead:
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
            raise PortfolioNotFoundError(
                f"Portfolio with ID {portfolio_id} not found for user {user_id}"
            )
        patch = payload.model_dump(exclude_unset=True)

        if "name" in patch:
            if patch["name"] is None:
                raise InvalidPortfolioDataError("Portfolio name cannot be set to None.")
            stripped = patch["name"].strip()
            if not stripped:
                raise InvalidPortfolioDataError(
                    "Portfolio name must contain non-whitespace text."
                )

            normalized_name = self._normalize_name(patch["name"])
            if self.repository.exists_by_name(
                normalized_name,
                user_id,
                exclude_id=portfolio_id,
            ):
                raise PortfolioAlreadyExistsError(
                    "Portfolio name already exists for this user."
                )
        updated_portfolio = self.repository.update_portfolio(
            portfolio_id, payload, user_id
        )
        self.repository.commit()
        self.repository.refresh(updated_portfolio)
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
            self.repository.commit()
            return True
        raise PortfolioNotFoundError(
            f"Portfolio with ID {portfolio_id} not found for user {user_id}"
        )
