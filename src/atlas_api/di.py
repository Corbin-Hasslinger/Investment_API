from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session

from atlas_api.repositories.portfolio_repository import PortfolioRepository

from .clients.finnhub_client import FinnhubClient
from .core.config import Settings, get_settings
from .core.db import get_session
from .schemas.user import CurrentUserRead
from .services.portfolio_service import PortfolioService
from .services.stock_service import StockService

__all__ = [
    "CurrentUserDI",
    "FinnhubClientDI",
    "PortfolioRepositoryDI",
    "PortfolioServiceDI",
    "SessionDI",
    "SettingsDI",
    "StockServiceDI",
]

type SettingsDI = Annotated[Settings, Depends(get_settings)]


def get_current_user() -> CurrentUserRead:
    """Temporary development user until authentication is implemented."""
    return CurrentUserRead(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="dev-user@atlas.local",
    )


type CurrentUserDI = Annotated[CurrentUserRead, Depends(get_current_user)]

def get_finnhub_client(settings: SettingsDI) -> FinnhubClient:
    """Dependency function to provide a FinnhubClient instance."""
    api_key = settings.finnhub_api_key
    if api_key is None:
        raise ValueError(
            "FINNHUB_API_KEY is required to initialize the Finnhub client."
        )
    return FinnhubClient(api_key=api_key.get_secret_value())

type FinnhubClientDI = Annotated[FinnhubClient, Depends(get_finnhub_client)]

def get_stock_service(finnhub_client: FinnhubClientDI) -> StockService:
    """Dependency function to provide a StockService instance."""
    return StockService(finnhub_client=finnhub_client)

type StockServiceDI = Annotated[StockService, Depends(get_stock_service)]

type SessionDI = Annotated[Session, Depends(get_session)]

def get_portfolio_repository(session: SessionDI):
    """Dependency function to provide a PortfolioRepository instance."""
    from .repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository(session=session)

type PortfolioRepositoryDI = Annotated[
    PortfolioRepository, Depends(get_portfolio_repository)
]

def get_portfolio_service(portfolio_repository: PortfolioRepositoryDI) -> PortfolioService:
    """Dependency function to provide a PortfolioService instance."""
    return PortfolioService(repository=portfolio_repository)

type PortfolioServiceDI = Annotated[PortfolioService, Depends(get_portfolio_service)]

