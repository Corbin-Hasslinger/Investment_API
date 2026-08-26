import logging
from typing import Any

from fastapi import APIRouter

from atlas_api.schemas.stock import StockQuote

from ..di import MarketDataServiceDI

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/market", 
    tags=["Market"]
    )

@router.get(
    "/quote/{symbol}", 
    response_model=StockQuote, 
    summary="Get stock quote for a given ticker symbol", 
    response_description="The stock quote for the given ticker symbol",
    )
async def get_stock_quote(
    symbol: str,
    market_service: MarketDataServiceDI
    ) -> StockQuote:
    """ Returns a formatted stock quote for the given ticker symbol, using the Finnhub API. """
    return await market_service.get_quote(symbol)

# @router.get(
#     "/basic-financials/{symbol}",
#     response_model=dict[str, Any],
#     summary="Get basic financials for a given ticker symbol",
#     response_description="The basic financials for the given ticker symbol",
#     )
# async def get_basic_financials(
#     symbol: str,
#     market_service: MarketDataServiceDI
#     ) -> dict[str, Any]:
#     """ Returns the basic financials for the given ticker symbol, using the Finnhub API. """
#     return await market_service.get_basic_financials(symbol)