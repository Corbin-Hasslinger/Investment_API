from uuid import UUID

from sqlmodel import col, select

from atlas_api.models.positions import Position
from atlas_api.schemas.position import PositionUpdate
from atlas_api.tools.errors import PositionNotFoundError


class PositionRepository:
    def __init__(self, session):
        self.session = session

    @property
    def model_type(self) -> type[Position]:
        return Position

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, position: Position) -> None:
        self.session.refresh(position)

    def create_position(self, position: Position) -> Position:
        self.session.add(position)
        self.session.flush()
        return position

    def get_position_by_id(
        self, position_id: UUID, portfolio_id: UUID
    ) -> Position | None:
        return self.session.exec(
            select(Position).where(
                Position.id == position_id, Position.portfolio_id == portfolio_id
            )
        ).first()

    def get_all_positions(self, portfolio_id: UUID) -> list[Position]:
        return self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(col(Position.created_at), col(Position.id))
        ).all()

    def update_position(
        self, position_id: UUID, portfolio_id: UUID, payload: PositionUpdate
    ) -> Position:
        position = self.get_position_by_id(position_id, portfolio_id)
        if position:
            for key, value in payload.model_dump(exclude_unset=True).items():
                setattr(position, key, value)
            self.session.add(position)
            self.session.flush()
            return position
        raise PositionNotFoundError(
            f"Position with ID {position_id} not found for portfolio {portfolio_id}"
        )

    def delete_position(self, position_id: UUID, portfolio_id: UUID) -> None:
        position = self.get_position_by_id(position_id, portfolio_id)
        if position:
            self.session.delete(position)
            self.session.flush()

    def exists_by_portfolio_and_security(self, symbol: str, portfolio_id: UUID) -> bool:
        return (
            self.session.exec(
                select(Position).where(
                    Position.portfolio_id == portfolio_id, Position.symbol == symbol
                )
            ).first()
            is not None
        )
