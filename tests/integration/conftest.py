from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.settings import settings
from app.database.sql_db import get_db
from app.database.valkey import get_valkey
from app.main import app


@pytest_asyncio.fixture
async def db_session():
    """Provides an isolated, shared in-memory SQLite database session."""
    # "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared"
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # (Your table creation block here: Base.metadata.create_all)
    async with engine.begin() as conn:
        from app.models import Base  # Adjust to your base model path
        await conn.run_sync(Base.metadata.create_all)
        
    session = AsyncSession(engine, expire_on_commit=False)
    yield session
    await session.close()


@pytest.fixture
def mock_valkey():
    """Provides a cleanly reset AsyncMock instance for caching operations."""
    mock = AsyncMock()
    mock.delete = AsyncMock()
    mock.setex = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def test_user_id() -> UUID:
    """Provides a reliable, fixed user ID context for the duration of a test."""
    return uuid4()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, mock_valkey):
    """Provides a standard, unauthenticated AsyncClient (Anonymous / Logged Out User)."""
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_valkey] = lambda v=mock_valkey: v

    # Mock application state attributes globally
    mock_pool = AsyncMock()
    app.state.valkey_pool = mock_pool
    app.state.s3_client = AsyncMock()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, test_user_id: UUID) -> AsyncClient:
    """Provides an authenticated AsyncClient (Logged In User).
    
    Bakes a cryptographically valid access token into cookies. Satisfies 
    CURRENT_USER_ID, LOGGED_IN_GUARD, and LOGGED_OUT_GUARD seamlessly.
    """
    # 1. Craft a valid JWT signed with your app's actual secret configurations
    payload = {
        "sub": str(test_user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "jti": f"test-jti-{uuid4().hex[:8]}"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # 2. Inject it straight into the client's cookie jar
    client.cookies.set("access_token", token)
    
    return client