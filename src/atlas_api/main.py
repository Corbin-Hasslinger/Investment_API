#!/usr/bin/env python3

from fastapi import FastAPI

from atlas_api.core.config import Settings, get_settings
from atlas_api.routes import API_ROUTERS


def create_app(settings: Settings) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title = settings.app_name,
    )

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
    # Add custom exception handlers here if needed

def register_lifecycle_hooks(app: FastAPI) -> None:
    """Register lifecycle hooks for the FastAPI application."""
    # Add startup and shutdown events here if needed

app = create_app(get_settings())