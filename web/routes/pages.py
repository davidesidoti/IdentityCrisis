"""
Page routes for rendering HTML templates.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shared import UserSession, get_config
from web.routes.dependencies import get_optional_user

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    user: UserSession | None = Depends(get_optional_user)
):
    """Home page."""
    config = get_config()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user": user,
            "config": config,
        }
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: UserSession | None = Depends(get_optional_user)
):
    """Dashboard page - shows user's servers."""
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    config = get_config()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "config": config,
        }
    )


@router.get("/dashboard/guild/{guild_id}", response_class=HTMLResponse)
async def guild_settings(
    request: Request,
    guild_id: int,
    user: UserSession | None = Depends(get_optional_user)
):
    """Guild settings page."""
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)
    
    config = get_config()
    return templates.TemplateResponse(
        "guild.html",
        {
            "request": request,
            "user": user,
            "config": config,
            "guild_id": guild_id,
        }
    )
