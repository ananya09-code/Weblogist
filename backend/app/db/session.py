from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .models import Base
from ..config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with SessionLocal() as session:
        yield session
