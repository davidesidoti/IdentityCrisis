"""
Page routes for rendering HTML templates.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from shared import UserSession, get_config
from web.routes.dependencies import get_optional_user

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="web/templates")

def _is_log_viewer(user: UserSession | None, config) -> bool:
    return bool(user and config.log_viewer_id and user.discord_id == config.log_viewer_id)


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
            "is_log_viewer": _is_log_viewer(user, config),
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
            "is_log_viewer": _is_log_viewer(user, config),
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
            "is_log_viewer": _is_log_viewer(user, config),
        }
    )


@router.get("/dashboard/logs", response_class=HTMLResponse)
async def logs(
    request: Request,
    user: UserSession | None = Depends(get_optional_user)
):
    """Bot logs page (restricted)."""
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    config = get_config()
    if not _is_log_viewer(user, config):
        raise HTTPException(status_code=403, detail="Not authorized")

    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "user": user,
            "config": config,
            "is_log_viewer": True,
        }
    )
