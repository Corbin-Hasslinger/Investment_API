from atlas_api.routes.stocks import router as stocks_router

API_ROUTERS = (
    stocks_router,
)

__all__ = ["API_ROUTERS"]