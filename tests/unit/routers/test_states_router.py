"""Unit tests for states router (mocked StateService)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.state import StateResponse
from app.services.state_service import StateConflictError, StateNotFoundError, StateService


def _state_response(id: int = 1, name: str = "California", abbreviation: str = "CA") -> StateResponse:
    return StateResponse(
        id=id,
        name=name,
        abbreviation=abbreviation,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_state_service() -> AsyncMock:
    return AsyncMock(spec=StateService)


@pytest.fixture
def client(mock_state_service: AsyncMock) -> TestClient:
    from app.dependencies import get_state_service, require_session_cookie

    async def override_get_state_service() -> StateService:
        return mock_state_service

    async def override_require_session_cookie() -> None:
        return None

    app.dependency_overrides[get_state_service] = override_get_state_service
    app.dependency_overrides[require_session_cookie] = override_require_session_cookie
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_states_200(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.list_states.return_value = [
        _state_response(1, "California", "CA"),
        _state_response(2, "New York", "NY"),
    ]

    response = client.get("/api/states")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["abbreviation"] == "CA"
    assert data[1]["abbreviation"] == "NY"
    mock_state_service.list_states.assert_awaited_once()


def test_get_state_200(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.get_state.return_value = _state_response(1, "California", "CA")

    response = client.get("/api/states/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["abbreviation"] == "CA"
    mock_state_service.get_state.assert_awaited_once_with(1)


def test_get_state_404(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.get_state.side_effect = StateNotFoundError(99)

    response = client.get("/api/states/99")

    assert response.status_code == 404
    assert "99" in response.json()["detail"]


def test_create_state_201(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.create_state.return_value = _state_response(1, "Texas", "TX")

    response = client.post(
        "/api/states",
        json={"name": "Texas", "abbreviation": "TX", "is_active": True},
    )

    assert response.status_code == 201
    assert response.json()["abbreviation"] == "TX"
    mock_state_service.create_state.assert_awaited_once()
    body = mock_state_service.create_state.await_args[0][0]
    assert body.name == "Texas" and body.abbreviation == "TX"


def test_create_state_400_conflict(client: TestClient, mock_state_service: AsyncMock) -> None:
    """Duplicate abbreviation returns 400 (implementation maps conflict to 400)."""
    mock_state_service.create_state.side_effect = StateConflictError("abbreviation already exists")

    response = client.post(
        "/api/states",
        json={"name": "Duplicate", "abbreviation": "CA", "is_active": True},
    )

    assert response.status_code == 400
    assert "detail" in response.json()


def test_update_state_200(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.update_state.return_value = _state_response(
        1, "Calif.", "CA"
    )

    response = client.put("/api/states/1", json={"name": "Calif."})

    assert response.status_code == 200
    mock_state_service.update_state.assert_awaited_once()
    call_args = mock_state_service.update_state.await_args[0]
    assert call_args[0] == 1
    assert call_args[1].name == "Calif."
    assert call_args[1].abbreviation is None


def test_update_state_404(client: TestClient, mock_state_service: AsyncMock) -> None:
    mock_state_service.update_state.side_effect = StateNotFoundError(99)

    response = client.put("/api/states/99", json={"name": "X"})

    assert response.status_code == 404
