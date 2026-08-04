import logging

from fastapi import APIRouter, HTTPException

from atlas_api.schemas.stock import StockQuote

from ..di import StockServiceDI

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix = "/stocks", 
    tags=["Stocks"]
    )

@router.get(
    "/{ticker}/quote", 
    response_model=StockQuote, 
    summary="Get stock quote for a given ticker symbol", 
    response_description="The stock quote for the given ticker symbol",
    )
async def get_stock_quote(
    ticker: str,
    stock_service: StockServiceDI
    ) -> StockQuote:
    """ Returns a formatted stock quote for the given ticker symbol, using the Finnhub API. """
    try:
        return await stock_service.fetch_stock_quote(ticker)
    except Exception as e:
        logger.exception("Error fetching stock quote for %s", ticker)
        raise HTTPException(
            status_code=500, 
            detail="Error fetching stock quote"
            ) from e