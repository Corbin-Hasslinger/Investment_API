from atlas_api.routes.stocks import router as stocks_router
from atlas_api.routes.users import router as users_router

API_ROUTERS = (
    stocks_router,
    users_router,
)

__all__ = ["API_ROUTERS"]