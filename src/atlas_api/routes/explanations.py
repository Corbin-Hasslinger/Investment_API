from uuid import UUID

from fastapi import APIRouter, status

from atlas_api.di import AIExplanationServiceDI, CurrentUserDI
from atlas_api.schemas.ai import PortfolioExplanationRead, SecurityExplanationRead

router = APIRouter(
    prefix="/explanations",
    tags=["Explanations"],
)


@router.post(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioExplanationRead,
    summary="Generate AI explanation for a specific portfolio",
    status_code=status.HTTP_200_OK,
)
async def generate_portfolio_explanation(
    portfolio_id: UUID, current_user: CurrentUserDI, service: AIExplanationServiceDI
) -> PortfolioExplanationRead:
    return await service.explain_portfolio(
        portfolio_id=portfolio_id, user_id=current_user.id
    )


@router.post(
    "/securities/{symbol}",
    response_model=SecurityExplanationRead,
    summary="Generate AI explanation for a specific security",
    status_code=status.HTTP_200_OK,
)
async def generate_security_explanation(
    symbol: str, service: AIExplanationServiceDI
) -> SecurityExplanationRead:
    return await service.explain_security(
        symbol=symbol,
    )
