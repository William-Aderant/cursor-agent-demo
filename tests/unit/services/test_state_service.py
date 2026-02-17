"""Unit tests for StateService (mocked repository)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.state import State
from app.schemas.state import StateCreate, StateUpdate
from app.services.state_service import (
    StateConflictError,
    StateNotFoundError,
    StateService,
)


def _make_state(
    id: int = 1,
    name: str = "California",
    abbreviation: str = "CA",
    is_active: bool = True,
) -> State:
    state = MagicMock(spec=State)
    state.id = id
    state.name = name
    state.abbreviation = abbreviation
    state.is_active = is_active
    state.created_at = datetime.now(timezone.utc)
    state.updated_at = datetime.now(timezone.utc)
    return state


@pytest.fixture
def repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def service(repo: AsyncMock) -> StateService:
    return StateService(repo)


@pytest.mark.asyncio
async def test_list_states_returns_all(service: StateService, repo: AsyncMock) -> None:
    s1 = _make_state(1, "California", "CA")
    s2 = _make_state(2, "New York", "NY")
    repo.list_all.return_value = [s1, s2]

    result = await service.list_states()

    assert len(result) == 2
    assert result[0].id == 1 and result[0].abbreviation == "CA"
    assert result[1].id == 2 and result[1].abbreviation == "NY"
    repo.list_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_state_returns_state(service: StateService, repo: AsyncMock) -> None:
    state = _make_state(1, "California", "CA")
    repo.get_by_id.return_value = state

    result = await service.get_state(1)

    assert result.id == 1
    assert result.name == "California"
    assert result.abbreviation == "CA"
    repo.get_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_state_raises_when_not_found(service: StateService, repo: AsyncMock) -> None:
    repo.get_by_id.return_value = None

    with pytest.raises(StateNotFoundError) as exc_info:
        await service.get_state(99)

    assert exc_info.value.state_id == 99


@pytest.mark.asyncio
async def test_create_state_success(service: StateService, repo: AsyncMock) -> None:
    repo.get_by_abbreviation.return_value = None
    created = _make_state(1, "Texas", "TX")
    repo.create.return_value = created

    body = StateCreate(name="Texas", abbreviation="TX", is_active=True)
    result = await service.create_state(body)

    assert result.id == 1
    assert result.abbreviation == "TX"
    repo.get_by_abbreviation.assert_awaited_once_with("TX")
    repo.create.assert_awaited_once_with(name="Texas", abbreviation="TX", is_active=True)


@pytest.mark.asyncio
async def test_create_state_raises_on_duplicate_abbreviation(
    service: StateService,
    repo: AsyncMock,
) -> None:
    repo.get_by_abbreviation.return_value = _make_state(1, "California", "CA")

    body = StateCreate(name="Another CA", abbreviation="CA", is_active=True)
    with pytest.raises(StateConflictError) as exc_info:
        await service.create_state(body)

    assert "already exists" in str(exc_info.value)
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_state_success(service: StateService, repo: AsyncMock) -> None:
    state = _make_state(1, "California", "CA")
    repo.get_by_id.return_value = state
    repo.get_by_abbreviation.return_value = None
    repo.update.return_value = state

    body = StateUpdate(name="Calif.")
    result = await service.update_state(1, body)

    assert result.id == 1
    repo.update.assert_awaited_once()
    call_kw = repo.update.await_args[1]
    assert call_kw["name"] == "Calif."
    assert call_kw["abbreviation"] is None
    assert call_kw["is_active"] is None


@pytest.mark.asyncio
async def test_update_state_raises_when_not_found(service: StateService, repo: AsyncMock) -> None:
    repo.get_by_id.return_value = None

    with pytest.raises(StateNotFoundError) as exc_info:
        await service.update_state(99, StateUpdate(name="X"))

    assert exc_info.value.state_id == 99


@pytest.mark.asyncio
async def test_update_state_raises_on_duplicate_abbreviation(
    service: StateService,
    repo: AsyncMock,
) -> None:
    state = _make_state(1, "California", "CA")
    other = _make_state(2, "New York", "NY")
    repo.get_by_id.return_value = state
    repo.get_by_abbreviation.return_value = other

    body = StateUpdate(abbreviation="NY")
    with pytest.raises(StateConflictError) as exc_info:
        await service.update_state(1, body)

    assert "already exists" in str(exc_info.value)
    repo.update.assert_not_awaited()
