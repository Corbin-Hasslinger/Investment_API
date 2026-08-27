from fastapi import APIRouter, status

from atlas_api.di import ResearchServiceDI
from atlas_api.schemas.research import CompanyResearchRead

router = APIRouter(
    prefix="/research",
    tags=["Research"],
)


@router.get(
    "/company/{symbol}",
    response_model=CompanyResearchRead,
    status_code=status.HTTP_200_OK,
    summary="Get research service",
    response_description="Research service response",
)
async def get_company_research(
    symbol: str, service: ResearchServiceDI
) -> CompanyResearchRead:
    """Return a combined company profile, financial metrics, and recent news."""
    return await service.get_company_research(symbol)
