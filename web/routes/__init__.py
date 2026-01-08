"""Routes package for web dashboard."""

from .api import router as api_router
from .auth import router as auth_router
from .pages import router as pages_router

__all__ = ["api_router", "auth_router", "pages_router"]
