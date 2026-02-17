"""Session repository — lookup by token for auth."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_valid_by_token(self, token: str) -> Session | None:
        """Return session if token exists and not expired."""
        result = await self._session.execute(
            select(Session).where(
                Session.token == token,
                Session.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()
