#!/usr/bin/env python3

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from atlas_api.core.config import Settings, get_settings
from atlas_api.routes import API_ROUTERS

from .tools.errors import (
    InvalidPortfolioDataError,
    InvalidPositionDataError,
    InvalidSecurityDataError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
    PositionAlreadyExistsError,
    PositionNotFoundError,
    SecurityAlreadyExistsError,
    SecurityNotFoundError,
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
    @app.exception_handler(SecurityAlreadyExistsError)
    async def handle_security_already_exists_error(_: Request, exc: SecurityAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "security_already_exists", "message": str(exc) or "Security already exists"}},
        )
    @app.exception_handler(SecurityNotFoundError)
    async def handle_security_not_found_error(_: Request, exc: SecurityNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": "security_not_found", "message": str(exc) or "Security not found"}},
        )
    @app.exception_handler(InvalidSecurityDataError)
    async def handle_invalid_security_data_error(_: Request, exc: InvalidSecurityDataError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {"code": "invalid_security_data", "message": str(exc) or "Invalid security data"}},
        )
    @app.exception_handler(PositionAlreadyExistsError)
    async def handle_position_already_exists_error(_: Request, exc: PositionAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "position_already_exists", "message": str(exc) or "Position already exists"}},
        )
    @app.exception_handler(PositionNotFoundError)
    async def handle_position_not_found_error(_: Request, exc: PositionNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": "position_not_found", "message": str(exc) or "Position not found"}},
        )
    @app.exception_handler(InvalidPositionDataError)
    async def handle_invalid_position_data_error(_: Request, exc: InvalidPositionDataError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {"code": "invalid_position_data", "message": str(exc) or "Invalid position data"}},
        )

def register_lifecycle_hooks(app: FastAPI) -> None:
    """Register lifecycle hooks for the FastAPI application."""
    # Add startup and shutdown events here if needed

app = create_app(get_settings())