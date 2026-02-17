"""State repository — async SQLAlchemy queries for states table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.state import State


class StateRepository:
    """Async repository for State CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[State]:
        """Return all states, order by name."""
        result = await self._session.execute(
            select(State).order_by(State.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, state_id: int) -> State | None:
        """Return one state by id or None."""
        result = await self._session.execute(
            select(State).where(State.id == state_id)
        )
        return result.scalar_one_or_none()

    async def get_by_abbreviation(self, abbreviation: str) -> State | None:
        """Return one state by abbreviation or None."""
        result = await self._session.execute(
            select(State).where(State.abbreviation == abbreviation)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, abbreviation: str, is_active: bool = True) -> State:
        """Create a state and return it (flush so id is set)."""
        state = State(
            name=name,
            abbreviation=abbreviation.upper(),
            is_active=is_active,
        )
        self._session.add(state)
        await self._session.flush()
        await self._session.refresh(state)
        return state

    async def update(
        self,
        state: State,
        *,
        name: str | None = None,
        abbreviation: str | None = None,
        is_active: bool | None = None,
    ) -> State:
        """Update state in place; return the same instance."""
        if name is not None:
            state.name = name
        if abbreviation is not None:
            state.abbreviation = abbreviation.upper()
        if is_active is not None:
            state.is_active = is_active
        await self._session.flush()
        await self._session.refresh(state)
        return state
