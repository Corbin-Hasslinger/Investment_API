#!/usr/bin/env python3

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from atlas_api.core.config import Settings, get_settings
from atlas_api.routes import API_ROUTERS

from .tools import (
    InvalidPortfolioDataError,
    InvalidPositionDataError,
    InvalidSecurityDataError,
    InvalidSymbolFormatError,
    PortfolioAlreadyExistsError,
    PortfolioNotFoundError,
    PositionAlreadyExistsError,
    PositionNotFoundError,
    SecurityAlreadyExistsError,
    SecurityNotFoundError,
    UnsupportedSymbolError,
    UpstreamRateLimitedError,
    UpstreamResponseError,
    UpstreamTimeoutError,
    UpstreamUnavailableError,
)


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
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
            content={
                "error": {
                    "code": "portfolio_not_found",
                    "message": str(exc) or "Portfolio not found",
                }
            },
        )

    @app.exception_handler(PortfolioAlreadyExistsError)
    async def handle_portfolio_already_exists_error(
        _: Request, exc: PortfolioAlreadyExistsError
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "portfolio_already_exists",
                    "message": str(exc) or "Portfolio already exists",
                }
            },
        )

    @app.exception_handler(InvalidPortfolioDataError)
    async def handle_invalid_portfolio_data_error(
        _: Request, exc: InvalidPortfolioDataError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "invalid_portfolio_data",
                    "message": str(exc) or "Invalid portfolio data",
                }
            },
        )

    @app.exception_handler(SecurityAlreadyExistsError)
    async def handle_security_already_exists_error(
        _: Request, exc: SecurityAlreadyExistsError
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "security_already_exists",
                    "message": str(exc) or "Security already exists",
                }
            },
        )

    @app.exception_handler(SecurityNotFoundError)
    async def handle_security_not_found_error(_: Request, exc: SecurityNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "security_not_found",
                    "message": str(exc) or "Security not found",
                }
            },
        )

    @app.exception_handler(InvalidSecurityDataError)
    async def handle_invalid_security_data_error(
        _: Request, exc: InvalidSecurityDataError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "invalid_security_data",
                    "message": str(exc) or "Invalid security data",
                }
            },
        )

    @app.exception_handler(PositionAlreadyExistsError)
    async def handle_position_already_exists_error(
        _: Request, exc: PositionAlreadyExistsError
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": "position_already_exists",
                    "message": str(exc) or "Position already exists",
                }
            },
        )

    @app.exception_handler(PositionNotFoundError)
    async def handle_position_not_found_error(_: Request, exc: PositionNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "position_not_found",
                    "message": str(exc) or "Position not found",
                }
            },
        )

    @app.exception_handler(InvalidPositionDataError)
    async def handle_invalid_position_data_error(
        _: Request, exc: InvalidPositionDataError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "invalid_position_data",
                    "message": str(exc) or "Invalid position data",
                }
            },
        )

    @app.exception_handler(InvalidSymbolFormatError)
    async def handle_invalid_symbol_format_error(
        _: Request, exc: InvalidSymbolFormatError
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "invalid_symbol_format",
                    "message": str(exc) or "Invalid symbol format",
                }
            },
        )

    @app.exception_handler(UnsupportedSymbolError)
    async def handle_unsupported_symbol_error(_: Request, exc: UnsupportedSymbolError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "unsupported_symbol",
                    "message": str(exc) or "Unsupported symbol",
                }
            },
        )

    @app.exception_handler(UpstreamTimeoutError)
    async def handle_upstream_timeout_error(_: Request, exc: UpstreamTimeoutError):
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": {
                    "code": "upstream_timeout",
                    "message": str(exc) or "Upstream API timeout",
                }
            },
        )

    @app.exception_handler(UpstreamRateLimitedError)
    async def handle_upstream_rate_limited_error(
        _: Request, exc: UpstreamRateLimitedError
    ):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "upstream_rate_limited",
                    "message": str(exc) or "Upstream API rate limited",
                }
            },
        )

    @app.exception_handler(UpstreamUnavailableError)
    async def handle_upstream_unavailable_error(
        _: Request, exc: UpstreamUnavailableError
    ):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "upstream_unavailable",
                    "message": str(exc) or "Upstream API unavailable",
                }
            },
        )

    @app.exception_handler(UpstreamResponseError)
    async def handle_upstream_response_error(_: Request, exc: UpstreamResponseError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": "upstream_response_error",
                    "message": str(exc)
                    or "Upstream API returned an unexpected response",
                }
            },
        )


def register_lifecycle_hooks(app: FastAPI) -> None:
    """Register lifecycle hooks for the FastAPI application."""
    # Add startup and shutdown events here if needed


app = create_app(get_settings())
