from uuid import UUID

from sqlalchemy import func
from sqlmodel import col, select

from atlas_api.models.portfolios import Portfolio
from atlas_api.schemas.portfolio import PortfolioUpdate
from atlas_api.tools.errors import PortfolioNotFoundError


class PortfolioRepository:
    def __init__(self, session):
        self.session = session

    @property
    def model_type(self) -> type[Portfolio]:
        return Portfolio

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, portfolio: Portfolio) -> None:
        self.session.refresh(portfolio)

    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self.session.add(portfolio)
        self.session.flush()
        return portfolio

    def get_portfolio_by_id(
        self, portfolio_id: UUID, user_id: UUID
    ) -> Portfolio | None:
        return self.session.exec(
            select(Portfolio).where(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            )
        ).first()

    def get_all_portfolios(self, user_id: UUID) -> list[Portfolio]:
        return self.session.exec(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(col(Portfolio.created_at).desc(), col(Portfolio.id).desc())
        ).all()

    def update_portfolio(
        self, portfolio_id: UUID, payload: PortfolioUpdate, user_id: UUID
    ) -> Portfolio:
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(portfolio, key, value)
        if portfolio:
            self.session.add(portfolio)
            self.session.flush()
            return portfolio
        raise PortfolioNotFoundError(
            f"Portfolio with ID {portfolio_id} not found for user {user_id}"
        )

    def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> None:
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio:
            self.session.delete(portfolio)
            self.session.flush()

    def exists_by_name(
        self, name: str, user_id: UUID, exclude_id: UUID | None = None
    ) -> bool:
        stmt = select(Portfolio).where(
            func.lower(Portfolio.name) == name.lower(),
            Portfolio.user_id == user_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(Portfolio.id != exclude_id)

        return self.session.exec(stmt).first() is not None
