"""
Dependencies for web routes.
"""

from datetime import datetime, timezone

from fastapi import Cookie, HTTPException
from sqlalchemy import select

from shared import UserSession, get_config, get_db
from web.discord_oauth import DiscordOAuth


async def get_current_user(session_id: str = Cookie(None)) -> UserSession:
    """
    Get the current authenticated user from session cookie.
    Raises HTTPException if not authenticated or token expired.
    """
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    db = get_db()
    async with db.async_session() as session:
        result = await session.execute(
            select(UserSession).where(UserSession.discord_id == int(session_id))
        )
        user_session = result.scalar_one_or_none()
        
        if not user_session:
            raise HTTPException(status_code=401, detail="Session not found")
        
        # Check if token is expired
        if DiscordOAuth.is_token_expired(user_session.token_expires_at):
            # Try to refresh the token
            config = get_config()
            oauth = DiscordOAuth(config)
            
            try:
                token_data = await oauth.refresh_token(user_session.refresh_token)
                user_session.access_token = token_data["access_token"]
                user_session.refresh_token = token_data["refresh_token"]
                user_session.token_expires_at = oauth.calculate_token_expiry(
                    token_data["expires_in"]
                )
                user_session.updated_at = datetime.now(timezone.utc)
                await session.commit()
                await session.refresh(user_session)
            except Exception:
                raise HTTPException(
                    status_code=401, 
                    detail="Session expired, please login again"
                )
        
        return user_session


async def get_optional_user(session_id: str = Cookie(None)) -> UserSession | None:
    """
    Get the current user if authenticated, None otherwise.
    Does not raise exceptions.
    """
    if not session_id:
        return None
    
    try:
        return await get_current_user(session_id)
    except HTTPException:
        return None
