"""FastAPI dependencies — DB session, repositories, services, auth."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.session_repository import SessionRepository
from app.repositories.state_repository import StateRepository
from app.services.state_service import StateService


async def require_session_cookie(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Raise 401 if the session cookie is missing or invalid (not in DB or expired)."""
    cookie_name = get_settings().AUTH_SESSION_COOKIE_NAME
    token = request.cookies.get(cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid session",
        )
    repo = SessionRepository(db)
    session = await repo.get_valid_by_token(token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid session",
        )
    return None


async def get_state_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> StateRepository:
    return StateRepository(session)


async def get_state_service(
    repo: Annotated[StateRepository, Depends(get_state_repository)],
) -> StateService:
    return StateService(repo)
