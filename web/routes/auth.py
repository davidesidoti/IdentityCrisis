"""
Authentication routes for Discord OAuth2.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from shared import UserSession, get_config, get_db
from web.discord_oauth import DiscordOAuth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """Redirect to Discord OAuth2 authorization."""
    config = get_config()
    return RedirectResponse(url=config.discord_oauth_url)


@router.get("/callback")
async def callback(request: Request, code: str = None, error: str = None):
    """Handle Discord OAuth2 callback."""
    if error:
        logger.error(f"OAuth error: {error}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    config = get_config()
    oauth = DiscordOAuth(config)
    
    try:
        # Exchange code for tokens
        token_data = await oauth.exchange_code(code)
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        
        # Get user info
        user = await oauth.get_user(access_token)
        
        # Save/update session in database
        db = get_db()
        async with db.async_session() as session:
            result = await session.execute(
                select(UserSession).where(UserSession.discord_id == int(user["id"]))
            )
            user_session = result.scalar_one_or_none()
            
            if user_session is None:
                user_session = UserSession(
                    discord_id=int(user["id"]),
                    username=user["username"],
                    avatar_url=oauth.get_avatar_url(user),
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_expires_at=oauth.calculate_token_expiry(expires_in),
                )
                session.add(user_session)
            else:
                user_session.username = user["username"]
                user_session.avatar_url = oauth.get_avatar_url(user)
                user_session.access_token = access_token
                user_session.refresh_token = refresh_token
                user_session.token_expires_at = oauth.calculate_token_expiry(expires_in)
                user_session.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
        
        # Set session cookie and redirect to dashboard
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="session_id",
            value=str(user["id"]),
            httponly=True,
            max_age=60 * 60 * 24 * 7,  # 7 days
            samesite="lax",
        )
        return response
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.get("/logout")
async def logout(request: Request):
    """Log out the user."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response
