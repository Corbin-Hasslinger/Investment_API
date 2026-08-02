from typing import Annotated

from fastapi import Depends

from atlas_api.clients.finnhub_client import FinnhubClient
from atlas_api.services.stock_service import StockService
from core.config import Settings

__all__ = [
    "FinnhubClientDI",
    "SettingsDI",
    "StockServiceDI"
]

def get_settings() -> Settings:
    """Dependency function to provide a Settings instance."""
    return Settings()

type SettingsDI = Annotated[Settings, Depends(get_settings)]

def get_finnhub_client(settings: SettingsDI) -> FinnhubClient:
    """Dependency function to provide a FinnhubClient instance."""
    return FinnhubClient(api_key=settings.finnhub_api_key)

type FinnhubClientDI = Annotated[FinnhubClient, Depends(get_finnhub_client)]

def get_stock_service(finnhub_client: FinnhubClientDI) -> StockService:
    """Dependency function to provide a StockService instance."""
    return StockService(finnhub_client=finnhub_client)

type StockServiceDI = Annotated[StockService, Depends(get_stock_service)]
