from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from sqlmodel import Session

from atlas_api.services.market_data_service import MarketDataService
from atlas_api.services.security_service import SecurityService

from .clients.finnhub_client import FinnhubClient
from .core.config import Settings, get_settings
from .core.db import get_session
from .repositories.portfolio_repository import PortfolioRepository
from .repositories.position_repository import PositionRepository
from .repositories.security_repository import SecurityRepository
from .schemas.user import CurrentUserRead
from .services.portfolio_service import PortfolioService
from .services.position_service import PositionService
from .services.stock_service import StockService
from .tools import PaginationParams

__all__ = [
    "CurrentUserDI",
    "FinnhubClientDI",
    "MarketDataServiceDI",
    "PaginationParams",
    "PortfolioRepositoryDI",
    "PortfolioServiceDI",
    "PositionRepositoryDI",
    "PositionServiceDI",
    "SecurityRepositoryDI",
    "SecurityServiceDI",
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

type SessionDI = Annotated[Session, Depends(get_session)]

def get_finnhub_client(settings: SettingsDI) -> FinnhubClient:
    """Dependency function to provide a FinnhubClient instance."""
    api_key = settings.finnhub_api_key
    if api_key is None:
        raise ValueError(
            "FINNHUB_API_KEY is required to initialize the Finnhub client."
        )
    return FinnhubClient(api_key=api_key.get_secret_value())

type FinnhubClientDI = Annotated[FinnhubClient, Depends(get_finnhub_client)]

def get_security_repository(session: SessionDI):
    """Dependency function to provide a SecurityRepository instance."""
    return SecurityRepository(session=session)

type SecurityRepositoryDI = Annotated[
    SecurityRepository, Depends(get_security_repository)
]

def get_security_service(
    security_repository: SecurityRepositoryDI,
    finnhub_client: FinnhubClientDI,
) -> SecurityService:
    """Dependency function to provide a SecurityService instance."""
    return SecurityService(
        security_repository=security_repository,
        finnhub_client=finnhub_client,
    )

type SecurityServiceDI = Annotated[SecurityService, Depends(get_security_service)]
def get_stock_service(
    finnhub_client: FinnhubClientDI,
    security_service: SecurityServiceDI,
) -> StockService:
    """Dependency function to provide a StockService instance."""
    return StockService(
        finnhub_client=finnhub_client,
        security_service=security_service,
    )

type StockServiceDI = Annotated[StockService, Depends(get_stock_service)]

def get_portfolio_repository(session: SessionDI):
    """Dependency function to provide a PortfolioRepository instance."""
    return PortfolioRepository(session=session)

type PortfolioRepositoryDI = Annotated[
    PortfolioRepository, Depends(get_portfolio_repository)
]

def get_portfolio_service(portfolio_repository: PortfolioRepositoryDI) -> PortfolioService:
    """Dependency function to provide a PortfolioService instance."""
    return PortfolioService(repository=portfolio_repository)

type PortfolioServiceDI = Annotated[PortfolioService, Depends(get_portfolio_service)]


def get_position_repository(session: SessionDI):
    """Dependency function to provide a PositionRepository instance."""
    return PositionRepository(session=session)

type PositionRepositoryDI = Annotated[
    PositionRepository, Depends(get_position_repository)
]

def get_position_service(
    position_repository: PositionRepositoryDI,
    portfolio_repository: PortfolioRepositoryDI,
    security_service: SecurityServiceDI,
) -> PositionService:
    """Dependency function to provide a PositionService instance."""
    return PositionService(
        position_repository=position_repository,
        portfolio_repository=portfolio_repository,
        security_service=security_service,
    )

type PositionServiceDI = Annotated[PositionService, Depends(get_position_service)]

def get_market_data_service(
    security_service: SecurityServiceDI,
    finnhub_client: FinnhubClientDI,
) -> MarketDataService:
    """Dependency function to provide a MarketDataService instance."""

    return MarketDataService(
        security_service=security_service,
        finnhub_client=finnhub_client,
    )
type MarketDataServiceDI = Annotated[
    MarketDataService, Depends(get_market_data_service)
]

def get_pagination_params(
        page: Annotated[int, Query(ge=1)] =1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 25
) -> PaginationParams:
    """Dependency function to provide pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)

type PaginationParamsDI = Annotated[PaginationParams, Depends(get_pagination_params)]