
from uuid import UUID

from fastapi import APIRouter, status

from atlas_api.di import PaginationParamsDI, PositionServiceDI
from atlas_api.schemas.position import PositionCreate, PositionRead, PositionUpdate
from atlas_api.tools.pagination import PaginatedResult

router = APIRouter(
    prefix="/portfolios/{portfolio_id}/positions",
    tags=["Positions"],
)

@router.post("", 
             summary="Create a new position", 
             response_model=PositionRead, 
             status_code=status.HTTP_201_CREATED
             )
def create_position(
    service: PositionServiceDI,
    payload: PositionCreate,
    portfolio_id: UUID,
) -> PositionRead:
    """Creates a new position for a given portfolio.
    Args:
        payload (PositionCreate): The data for the new position.
        portfolio_id (UUID): The ID of the portfolio to which the position belongs.
    Returns:
        PositionRead: The created position with its details.
    """
    return service.create_position(payload, portfolio_id)

@router.get("", 
            summary="Get all positions", 
            response_model=PaginatedResult[PositionRead], 
            status_code=status.HTTP_200_OK
            )
def get_all_positions(
    service: PositionServiceDI,
    portfolio_id: UUID,
    pagination: PaginationParamsDI,
) -> PaginatedResult[PositionRead]:
    """Retrieves all positions for a given portfolio.
    Supports pagination through query parameters.
    Args:
        service (PositionService): The position service instance.
        portfolio_id (UUID): The ID of the portfolio to retrieve positions for.
        pagination (PaginationParams): Pagination parameters (page and page_size).
    Returns:
        PaginatedResult[Position]: A paginated collection of positions for the given portfolio.
    """
    return service.get_all_positions(portfolio_id, pagination)

@router.get("/{position_id}", 
            summary="Get a specific position by ID", 
            response_model=PositionRead, 
            status_code=status.HTTP_200_OK
            )
def get_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
) -> PositionRead:
    """Retrieves a specific position by its ID.
    Args:
        service (PositionService): The position service instance.
        position_id (UUID): The ID of the position to retrieve.
    Returns:
        PositionRead: The details of the requested position.
    """
    return service.get_position(position_id, portfolio_id)

@router.patch("/{position_id}", 
              summary="Update a specific position by ID", 
              response_model=PositionRead, 
              status_code=status.HTTP_200_OK
              )
def update_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
    payload: PositionUpdate,
) -> PositionRead:
    """Updates a specific position by its ID.
    Args:
        service (PositionService): The position service instance.
        position_id (UUID): The ID of the position to update.
        payload (PositionUpdate): The data to update the position with.
    Returns:
        PositionRead: The updated position with its details.
    """
    return service.update_position(position_id, portfolio_id, payload)

@router.delete("/{position_id}", 
               summary="Delete a specific position by ID",
               status_code=status.HTTP_204_NO_CONTENT
                )
def delete_position(
    service: PositionServiceDI,
    position_id: UUID,
    portfolio_id: UUID,
) -> None:
    """Deletes a specific position by its ID.
    Args:
        service (PositionService): The position service instance.
        position_id (UUID): The ID of the position to delete.
        portfolio_id (UUID): The ID of the portfolio the position belongs to.
    Returns:
        None
    """
    service.delete_position(position_id, portfolio_id)
