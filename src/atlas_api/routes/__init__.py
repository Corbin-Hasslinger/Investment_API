from atlas_api.routes.portfolios import router as portfolios_router
from atlas_api.routes.positions import router as positions_router
from atlas_api.routes.research import router as research_router
from atlas_api.routes.stocks import router as stocks_router
from atlas_api.routes.users import router as users_router

API_ROUTERS = (
    stocks_router,
    users_router,
    portfolios_router,
    positions_router,
    research_router,
)

__all__ = ["API_ROUTERS"]