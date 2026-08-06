#!/usr/bin/env python3

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from atlas_api.core.config import Settings, get_settings
from atlas_api.routes import API_ROUTERS

from .tools.errors import (
    InvalidPortfolioDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
)


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title = settings.app_name,
    )

    @app.get("/")
    async def read_root() -> dict[str, str]:
        return {"status": "ok"}

    map_routers(app)
    register_exception_handlers(app)
    register_lifecycle_hooks(app)

    return app

def map_routers(app: FastAPI) -> None:
    """Map the routers to the FastAPI application."""
    for router in API_ROUTERS:
        app.include_router(router)

def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the FastAPI application."""
    @app.exception_handler(PortfolioNotFoundError)
    async def handle_portfolio_not_found_error(_: Request, exc: PortfolioNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": "portfolio_not_found", "message": str(exc) or "Portfolio not found"}},
        )
    @app.exception_handler(PortfolioAlreadyExistsError)
    async def handle_portfolio_already_exists_error(_: Request, exc: PortfolioAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "portfolio_already_exists", "message": str(exc) or "Portfolio already exists"}},
        )

    @app.exception_handler(InvalidPortfolioDataError)
    async def handle_invalid_portfolio_data_error(_: Request, exc: InvalidPortfolioDataError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {"code": "invalid_portfolio_data", "message": str(exc) or "Invalid portfolio data"}},
        )

def register_lifecycle_hooks(app: FastAPI) -> None:
    """Register lifecycle hooks for the FastAPI application."""
    # Add startup and shutdown events here if needed

app = create_app(get_settings())