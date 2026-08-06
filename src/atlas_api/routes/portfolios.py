

from uuid import UUID

from fastapi import APIRouter, status

from atlas_api.di import CurrentUserDI, PortfolioServiceDI
from atlas_api.schemas.portfolio import PortfolioCreate, PortfolioRead, PortfolioUpdate

router = APIRouter(
    prefix="/portfolios",
    tags=["Portfolios"],
)

@router.post(
    "",
    response_model=PortfolioRead,
    summary="Create a new portfolio",
    status_code = status.HTTP_201_CREATED,
)
def create_portfolio(
    payload: PortfolioCreate, 
    service: PortfolioServiceDI,
    current_user: CurrentUserDI
) -> PortfolioRead:
    """Creates a new portfolio."""
    return service.create_portfolio(payload, current_user.id)

@router.get(
    "",
    response_model=list[PortfolioRead],
    summary="Get all portfolios",
    status_code = status.HTTP_200_OK,
)
def get_all_portfolios(
    service: PortfolioServiceDI,
    current_user: CurrentUserDI
) -> list[PortfolioRead]:
    """Retrieves all portfolios for the current user."""
    return service.get_all_portfolios(current_user.id)

@router.get("/{portfolio_id}",
    response_model=PortfolioRead,
    summary="Get a specific portfolio by ID",
    status_code=status.HTTP_200_OK,
)
def get_portfolio(
    portfolio_id: UUID,
    service: PortfolioServiceDI,
    current_user: CurrentUserDI
) -> PortfolioRead:
    """Retrieves a specific portfolio by its ID."""
    return service.get_portfolio(portfolio_id, current_user.id)

@router.patch("/{portfolio_id}",
    response_model=PortfolioRead,
    summary="Update a specific portfolio by ID",
    status_code=status.HTTP_200_OK,
)
def update_portfolio(
    portfolio_id: UUID,
    payload: PortfolioUpdate,
    service: PortfolioServiceDI,
    current_user: CurrentUserDI
) -> PortfolioRead:
    """Updates a specific portfolio by its ID."""
    return service.update_portfolio(portfolio_id, payload, current_user.id)

@router.delete("/{portfolio_id}",
    summary="Delete a specific portfolio by ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_portfolio(
    portfolio_id: UUID,
    service: PortfolioServiceDI,
    current_user: CurrentUserDI
) -> None:
    """Deletes a specific portfolio by its ID."""
    service.delete_portfolio(portfolio_id, current_user.id)
