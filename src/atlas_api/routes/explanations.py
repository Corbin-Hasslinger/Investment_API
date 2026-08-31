from uuid import UUID

from fastapi import APIRouter, status

from atlas_api.di import AIExplanationServiceDI, CurrentUserDI
from atlas_api.schemas.ai import PortfolioExplanationRead, SecurityExplanationRead

router = APIRouter(
    prefix="/explanations",
    tags=["Explanations"],
)


@router.get(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioExplanationRead,
    summary="Get AI-generated explanation for a specific portfolio",
    status_code=status.HTTP_200_OK,
)
async def get_portfolio_explanation(
    portfolio_id: UUID, current_user: CurrentUserDI, service: AIExplanationServiceDI
) -> PortfolioExplanationRead:
    return await service.explain_portfolio(
        portfolio_id=portfolio_id, user_id=current_user.id
    )


@router.get(
    "/securities/{symbol}",
    response_model=SecurityExplanationRead,
    summary="Get AI-generated explanation for a specific security",
    status_code=status.HTTP_200_OK,
)
async def get_security_explanation(
    symbol: str, service: AIExplanationServiceDI
) -> SecurityExplanationRead:
    return await service.explain_security(
        symbol=symbol,
    )
