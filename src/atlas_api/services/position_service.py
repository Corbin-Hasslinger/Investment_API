
import uuid
from uuid import UUID

from atlas_api.models.positions import Position
from atlas_api.repositories.portfolio_repository import PortfolioRepository
from atlas_api.repositories.position_repository import PositionRepository
from atlas_api.repositories.security_repository import SecurityRepository
from atlas_api.schemas.position import PositionCreate, PositionRead, PositionUpdate
from atlas_api.tools.errors import (
    PortfolioNotFoundError,
    PositionAlreadyExistsError,
    PositionNotFoundError,
    SecurityNotFoundError,
)
from atlas_api.tools.pagination import PaginatedResult, PaginationParams


class PositionService:
    def __init__(
        self,
        position_repository: PositionRepository,
        security_repository: SecurityRepository,
        portfolio_repository: PortfolioRepository,
    ):
        self.position_repository = position_repository
        self.security_repository = security_repository
        self.portfolio_repository = portfolio_repository

    def _to_read(self, model: Position) -> PositionRead:
        return PositionRead.model_validate(model, from_attributes=True)

    def _ensure_portfolio_owned_by_user(self, portfolio_id: UUID, user_id: UUID) -> None:
        portfolio = self.portfolio_repository.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio is None:
            raise PortfolioNotFoundError(
                f"Portfolio with ID {portfolio_id} not found for user {user_id}"
            )

    def create_position(self, payload: PositionCreate, portfolio_id: UUID, user_id: UUID) -> PositionRead:
        """Creates a new position for a portfolio owned by the current user."""
        self._ensure_portfolio_owned_by_user(portfolio_id, user_id)

        if not self.security_repository.get_security_by_id(payload.security_id):
            raise SecurityNotFoundError(f"Security with ID {payload.security_id} does not exist")
        if self.position_repository.exists_by_portfolio_and_security(payload.security_id, portfolio_id):
            raise PositionAlreadyExistsError(
                f"Position with security ID {payload.security_id} and portfolio_id {portfolio_id} already exists"
            )

        position_id = uuid.uuid4()
        position = self.position_repository.create_position(
            Position(
                id=position_id,
                portfolio_id=portfolio_id,
                security_id=payload.security_id,
                shares=payload.shares,
                average_cost=payload.average_cost,
            )
        )
        self.position_repository.commit()
        self.position_repository.refresh(position)
        return self._to_read(position)

    def get_all_positions(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        pagination: PaginationParams,
    ) -> PaginatedResult[PositionRead]:
        """Retrieves all positions for a portfolio owned by the current user."""
        self._ensure_portfolio_owned_by_user(portfolio_id, user_id)
        positions = self.position_repository.get_all_positions(portfolio_id)
        total = len(positions)
        start = (pagination.page - 1) * pagination.page_size
        end = start + pagination.page_size
        page_items = positions[start:end]
        return PaginatedResult(
            items=[self._to_read(position) for position in page_items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def get_position(self, position_id: UUID, portfolio_id: UUID, user_id: UUID) -> PositionRead:
        """Retrieves a specific position only if the portfolio belongs to the current user."""
        self._ensure_portfolio_owned_by_user(portfolio_id, user_id)
        position = self.position_repository.get_position_by_id(position_id, portfolio_id)
        if position:
            return self._to_read(position)
        raise PositionNotFoundError(
            f"Position with ID {position_id} not found for portfolio {portfolio_id}"
        )

    def update_position(
        self,
        position_id: UUID,
        portfolio_id: UUID,
        user_id: UUID,
        payload: PositionUpdate,
    ) -> PositionRead:
        """Updates a specific position only if the portfolio belongs to the current user."""
        self._ensure_portfolio_owned_by_user(portfolio_id, user_id)
        position = self.position_repository.get_position_by_id(position_id, portfolio_id)
        if not position:
            raise PositionNotFoundError(
                f"Position with ID {position_id} not found for portfolio {portfolio_id}"
            )
        updated_position = self.position_repository.update_position(position_id, portfolio_id, payload)
        self.position_repository.commit()
        self.position_repository.refresh(updated_position)
        return self._to_read(updated_position)

    def delete_position(self, position_id: UUID, portfolio_id: UUID, user_id: UUID) -> bool:
        """Deletes a specific position only if the portfolio belongs to the current user."""
        self._ensure_portfolio_owned_by_user(portfolio_id, user_id)
        position = self.position_repository.get_position_by_id(position_id, portfolio_id)
        if not position:
            raise PositionNotFoundError(
                f"Position with ID {position_id} not found for portfolio {portfolio_id}"
            )
        self.position_repository.delete_position(position_id, portfolio_id)
        self.position_repository.commit()
        return True
