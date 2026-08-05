from fastapi import APIRouter

from atlas_api.di import CurrentUserDI
from atlas_api.schemas.user import CurrentUserRead

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=CurrentUserRead,
    summary="Get current user",
    response_description="The current authenticated user",
)
def get_current_user_profile(current_user: CurrentUserDI) -> CurrentUserRead:
    """Returns the current user identity from dependency injection."""
    return CurrentUserRead(id=current_user.id, email=current_user.email)
