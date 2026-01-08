"""
Shared database module for IdentityCrisis.
Uses SQLAlchemy async with PostgreSQL.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, JSON, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models."""
    pass


class Guild(Base):
    """Server/Guild configuration."""
    __tablename__ = "guilds"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Discord guild ID
    name: Mapped[str] = mapped_column(String(100))
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Settings
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    restore_on_leave: Mapped[bool] = mapped_column(Boolean, default=True)
    immunity_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    nicknames: Mapped[list["Nickname"]] = relationship(
        back_populates="guild", 
        cascade="all, delete-orphan"
    )
    excluded_channels: Mapped[list["ExcludedChannel"]] = relationship(
        back_populates="guild",
        cascade="all, delete-orphan"
    )
    custom_channels: Mapped[list["CustomChannel"]] = relationship(
        back_populates="guild",
        cascade="all, delete-orphan"
    )


class Nickname(Base):
    """Custom nicknames for a guild."""
    __tablename__ = "nicknames"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"))
    nickname: Mapped[str] = mapped_column(String(32))  # Discord nickname limit
    
    # Relationship
    guild: Mapped["Guild"] = relationship(back_populates="nicknames")


class ExcludedChannel(Base):
    """Voice channels excluded from nickname chaos."""
    __tablename__ = "excluded_channels"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column(String(100))
    
    # Relationship
    guild: Mapped["Guild"] = relationship(back_populates="excluded_channels")
    

class CustomChannel(Base):
    """Voice channels with custom nickname rules."""
    __tablename__ = "custom_channels"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"))
    channel_id: Mapped[int] = mapped_column(BigInteger)
    channel_name: Mapped[str] = mapped_column(String(100))
    # Rules stored as JSON array, e.g. [{"type": "reverse"}, {"type": "prefix", "value": "[AFK]"}]
    rules: Mapped[list] = mapped_column(JSON, default=list)
    
    # Relationship
    guild: Mapped["Guild"] = relationship(back_populates="custom_channels")


class UserSession(Base):
    """Web dashboard user sessions."""
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )


class Database:
    """Database connection manager."""
    
    def __init__(self, database_url: str):
        # Convert postgres:// to postgresql+asyncpg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, 
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close database connection."""
        await self.engine.dispose()


# Global database instance (initialized in main)
db: Optional[Database] = None


async def init_database(database_url: str) -> Database:
    """Initialize the database connection."""
    global db
    db = Database(database_url)
    await db.create_tables()
    return db


def get_db() -> Database:
    """Get the database instance."""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db
