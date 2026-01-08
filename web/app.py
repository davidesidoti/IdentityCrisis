"""
FastAPI web application for IdentityCrisis dashboard.
"""

import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web.routes import api_router, auth_router, pages_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="IdentityCrisis Dashboard",
        description="Web dashboard for managing the IdentityCrisis Discord bot",
        version="1.0.0",
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(api_router)
    app.include_router(pages_router)
    
    @app.on_event("startup")
    async def startup():
        logger.info("Web dashboard starting up...")
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Web dashboard shutting down...")
    
    return app
