"""State service — business logic for states endpoint group."""

from __future__ import annotations

from app.repositories.state_repository import StateRepository
from app.schemas.state import StateCreate, StateUpdate, StateResponse


class StateNotFoundError(Exception):
    """State not found by id."""

    def __init__(self, state_id: int) -> None:
        self.state_id = state_id
        super().__init__(f"State not found: id={state_id}")


class StateConflictError(Exception):
    """Duplicate abbreviation or other conflict."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class StateService:
    """Business logic for state CRUD."""

    def __init__(self, repository: StateRepository) -> None:
        self._repo = repository

    async def list_states(self) -> list[StateResponse]:
        """Return all states."""
        states = await self._repo.list_all()
        return [StateResponse.model_validate(s) for s in states]

    async def get_state(self, state_id: int) -> StateResponse:
        """Return one state by id; raise StateNotFoundError if missing."""
        state = await self._repo.get_by_id(state_id)
        if state is None:
            raise StateNotFoundError(state_id)
        return StateResponse.model_validate(state)

    async def create_state(self, body: StateCreate) -> StateResponse:
        """Create a state; raise StateConflictError if abbreviation already exists."""
        existing = await self._repo.get_by_abbreviation(body.abbreviation)
        if existing is not None:
            raise StateConflictError(
                f"State with abbreviation '{body.abbreviation}' already exists"
            )
        state = await self._repo.create(
            name=body.name,
            abbreviation=body.abbreviation,
            is_active=body.is_active,
        )
        return StateResponse.model_validate(state)

    async def update_state(self, state_id: int, body: StateUpdate) -> StateResponse:
        """Update a state; raise StateNotFoundError or StateConflictError."""
        state = await self._repo.get_by_id(state_id)
        if state is None:
            raise StateNotFoundError(state_id)
        if body.abbreviation is not None:
            other = await self._repo.get_by_abbreviation(body.abbreviation)
            if other is not None and other.id != state_id:
                raise StateConflictError(
                    f"State with abbreviation '{body.abbreviation}' already exists"
                )
        updated = await self._repo.update(
            state,
            name=body.name,
            abbreviation=body.abbreviation,
            is_active=body.is_active,
        )
        return StateResponse.model_validate(updated)
