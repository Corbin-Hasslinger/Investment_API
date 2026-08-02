from typing import Annotated

from fastapi import Depends

from atlas_api.services.stock_service import StockService

__all__ = [
    "StockServiceDI"
]
def get_stock_service() -> StockService:
    """Dependency function to provide a StockService instance."""
    return StockService()

StockServiceDI = Annotated[StockService, Depends(get_stock_service)]