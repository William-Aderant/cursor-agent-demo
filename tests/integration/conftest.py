"""Integration test fixtures: async client, DB session in a transaction (rollback for isolation)."""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.session import Session as SessionModel

# Token and cookie for authenticated requests
INTEGRATION_TEST_TOKEN = "integration-test-token"


async def _create_auth_session(session: AsyncSession) -> None:
    """Insert a valid session row so cookie auth passes (same transaction)."""
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    auth_session = SessionModel(
        token=INTEGRATION_TEST_TOKEN,
        user_id="integration-test-user",
        email="test@example.com",
        expires_at=expires,
    )
    session.add(auth_session)
    await session.flush()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an AsyncSession inside a transaction that is rolled back after the test.
    Engine is created in the test's event loop to avoid "attached to different loop" errors.
    """
    engine = create_async_engine(
        get_settings().ASYNC_DATABASE_URL,
        echo=False,
    )
    try:
        async with engine.connect() as conn:
            await conn.begin()
            async with AsyncSession(
                bind=conn,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            ) as session:
                yield session
            await conn.rollback()
    finally:
        await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    httpx.AsyncClient against the FastAPI app, with get_db overridden to use
    the transactional db_session. Each test runs in an isolated transaction (rollback).
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def auth_client(client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    """
    Same as client but with a valid session row in the DB and cookie set on the client
    so requests are authenticated.
    """
    await _create_auth_session(db_session)
    await db_session.flush()
    cookie_name = get_settings().AUTH_SESSION_COOKIE_NAME
    client.cookies.set(cookie_name, INTEGRATION_TEST_TOKEN)
    return client
