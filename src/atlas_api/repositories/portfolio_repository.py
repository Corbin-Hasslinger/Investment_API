
from uuid import UUID

from sqlmodel import select

from atlas_api.models.portfolios import Portfolio
from atlas_api.schemas.portfolio import PortfolioUpdate


class PortfolioRepository:
    def __init__(self, session):
        self.session = session

    @property
    def model_type(self) -> type[Portfolio]:
        return Portfolio
    
    def create_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self.session.add(portfolio)
        self.session.commit()
        self.session.refresh(portfolio)
        return portfolio
    def get_portfolio_by_id(self, portfolio_id: UUID, user_id: UUID)  -> Portfolio | None:
        return self.session.exec(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id
            )
        ).first()
    def get_all_portfolios(self, user_id: UUID) -> list[Portfolio]:
        return self.session.exec(
            select(Portfolio).where(
                Portfolio.user_id == user_id
            )
        ).all()
    def update_portfolio(self, portfolio_id: UUID, payload: PortfolioUpdate, user_id: UUID) -> None:
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(portfolio, key, value)
        self.session.add(portfolio) 
        self.session.commit()
    def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> None:
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        if portfolio:
            self.session.delete(portfolio)
            self.session.commit()
        


