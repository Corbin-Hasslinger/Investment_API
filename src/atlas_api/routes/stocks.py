import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from atlas_api.schemas.stock import StockQuote
from atlas_api.tools.errors import (
    InvalidSymbolFormatError,
    UnsupportedSymbolError,
    UpstreamRateLimitedError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)

from ..di import MarketDataServiceDI, StockServiceDI

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
    try:
        return await market_service.get_quote(symbol)
    except InvalidSymbolFormatError as e:
        logger.warning("Invalid symbol format: %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except UnsupportedSymbolError as e:
        logger.warning("Unsupported symbol: %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except UpstreamTimeoutError as e:
        logger.error("Finnhub timeout for %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data service timed out. Please try again.",
        ) from e
    except UpstreamRateLimitedError as e:
        logger.warning("Finnhub rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests to market data service. Please retry later.",
        ) from e
    except UpstreamUnavailableError as e:
        logger.error("Finnhub unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data service unavailable. Please try again later.",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error fetching quote for %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e

        
@router.get(
    "/validate/{symbol}",
    summary="Validate a given ticker symbol",
    response_description="Returns true if the ticker symbol is valid, false otherwise",
    )
async def validate_ticker_symbol(
    symbol: str,
    stock_service: StockServiceDI
    ) -> dict[str, Any]:
    """ Validates a given ticker symbol by checking if it exists in the Finnhub API. """
    try:
        return await stock_service.validate_ticker_symbol(symbol)
    except InvalidSymbolFormatError as e:
            logger.warning("Invalid symbol format: %s", symbol)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
    except UnsupportedSymbolError as e:
        logger.warning("Unsupported symbol: %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except UpstreamTimeoutError as e:
        logger.error("Finnhub timeout for %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data service timed out. Please try again.",
        ) from e
    except UpstreamRateLimitedError as e:
        logger.warning("Finnhub rate limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests to market data service. Please retry later.",
        ) from e
    except UpstreamUnavailableError as e:
        logger.error("Finnhub unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data service unavailable. Please try again later.",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error fetching quote for %s", symbol)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e