from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from .clients.finnhub_client import FinnhubClient
from .core.config import Settings, get_settings
from .core.db import get_session
from .services.stock_service import StockService

__all__ = [
    "FinnhubClientDI",
    "SessionDI",
    "SettingsDI",
    "StockServiceDI"
]

type SettingsDI = Annotated[Settings, Depends(get_settings)]

def get_finnhub_client(settings: SettingsDI) -> FinnhubClient:
    """Dependency function to provide a FinnhubClient instance."""
    api_key = settings.finnhub_api_key
    assert api_key is not None
    return FinnhubClient(api_key=api_key.get_secret_value())

type FinnhubClientDI = Annotated[FinnhubClient, Depends(get_finnhub_client)]

def get_stock_service(finnhub_client: FinnhubClientDI) -> StockService:
    """Dependency function to provide a StockService instance."""
    return StockService(finnhub_client=finnhub_client)

type StockServiceDI = Annotated[StockService, Depends(get_stock_service)]

type SessionDI = Annotated[Session, Depends(get_session)]