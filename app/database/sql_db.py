from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import settings
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = settings.DB_URL
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(expire_on_commit=False, bind=engine, class_=AsyncSession)

async def get_db():
    async with SessionLocal() as session:
        yield session

async def create_db_tables():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)

DB_SESSION = Annotated[AsyncSession, Depends(get_db)]