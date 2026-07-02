from contextlib import AsyncExitStack, asynccontextmanager

import aioboto3
from botocore.config import Config
from fastapi import FastAPI
from valkey.asyncio import ConnectionPool

from app.core.settings import settings
from app.database.sql_db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # await create_db_tables()

    valkey_pool = ConnectionPool.from_url(settings.VALKEY_URL, decode_responses=True)
    app.state.valkey_pool = valkey_pool

    async with AsyncExitStack() as stack:
        session = aioboto3.Session()
        s3_config = Config(signature_version="s3v4", s3={"addressing_style": "virtual"})
        s3_client = await stack.enter_async_context(
            session.client("s3", region_name=settings.AWS_REGION, config=s3_config)
        )
        app.state.s3_client = s3_client

        yield

    await valkey_pool.disconnect()
    await engine.dispose()
