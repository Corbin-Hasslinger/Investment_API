from uuid import UUID

from fastapi import APIRouter, status

from atlas_api.di import CurrentUserDI, PaginationParamsDI, PositionServiceDI
from atlas_api.schemas.position import PositionCreate, PositionRead, PositionUpdate
from atlas_api.tools.pagination import PaginatedResult

router = APIRouter(
    prefix="/portfolios/{portfolio_id}/positions",
    tags=["Positions"],
)


@router.post(
    "",
    summary="Create a new position",
    response_model=PositionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_position(
    service: PositionServiceDI,
    payload: PositionCreate,
    portfolio_id: UUID,
    current_user: CurrentUserDI,
) -> PositionRead:
    """Creates a new position for a portfolio owned by the current user."""
    return await service.create_position(payload, portfolio_id, current_user.id)


@router.get(
    "",
    summary="Get all positions",
    response_model=PaginatedResult[PositionRead],
    status_code=status.HTTP_200_OK,
)
def get_all_positions(
    service: PositionServiceDI,
    portfolio_id: UUID,
    current_user: CurrentUserDI,
    pagination: PaginationParamsDI,
) -> PaginatedResult[PositionRead]:
    """Retrieves all positions for a portfolio owned by the current user."""
    return service.get_all_positions(portfolio_id, current_user.id, pagination)


@router.get(
    "/{position_id}",
    summary="Get a specific position by ID",
    response_model=PositionRead,
    status_code=status.HTTP_200_OK,
)
def get_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
    current_user: CurrentUserDI,
) -> PositionRead:
    """Retrieves a specific position by its ID, restricted to the current user's portfolio."""
    return service.get_position(position_id, portfolio_id, current_user.id)


@router.patch(
    "/{position_id}",
    summary="Update a specific position by ID",
    response_model=PositionRead,
    status_code=status.HTTP_200_OK,
)
def update_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
    current_user: CurrentUserDI,
    payload: PositionUpdate,
) -> PositionRead:
    """Updates a specific position only when it belongs to the current user's portfolio."""
    return service.update_position(position_id, portfolio_id, current_user.id, payload)


@router.delete(
    "/{position_id}",
    summary="Delete a specific position by ID",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
    current_user: CurrentUserDI,
) -> None:
    """Deletes a specific position only when it belongs to the current user's portfolio."""
    service.delete_position(position_id, portfolio_id, current_user.id)
