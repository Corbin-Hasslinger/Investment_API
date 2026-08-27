# from fastapi import APIRouter, status

# from atlas_api.schemas.security import SecurityCreate, SecurityRead

# router = APIRouter(
#     prefix="/securities",
#     tags=["Securities"],
# )

# @router.post("",
#              summary="Create a new security",
#              response_model=SecurityRead,
#              status_code=status.HTTP_201_CREATED)
# def create_security(
#     payload: SecurityCreate,
# ) -> SecurityRead:
#     """Creates a new security."""
#     # Placeholder implementation; replace with actual logic
#     return SecurityRead(**payload.dict())
