from fastapi import APIRouter, status

from atlas_api.di import ScreenerServiceDI
from atlas_api.schemas.stock import StockScreenerRead, StockScreenerRequest

router = APIRouter(prefix="/screeners", tags=["Screeners"])


@router.post(
    "/stocks",
    response_model=StockScreenerRead,
    status_code=status.HTTP_200_OK,
)
async def screen_stocks(
    request: StockScreenerRequest, service: ScreenerServiceDI
) -> StockScreenerRead:
    """Screens stocks based on the provided criteria."""
    return await service.screen_stocks(request)
