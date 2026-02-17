"""
Integration tests for States API (contracts.md).

Covers: happy path, 401, 400/422 (validation), 404, 409 (conflict → 400 in implementation).
Uses httpx.AsyncClient and transactional DB isolation (rollback per test).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_states_401_without_cookie(client: AsyncClient) -> None:
    """Without session cookie, GET /api/states returns 401."""
    response = await client.get("/api/states")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_list_states_200_empty(auth_client: AsyncClient) -> None:
    """With valid cookie, GET /api/states returns 200 and list (empty if no data)."""
    response = await auth_client.get("/api/states")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_state_401_without_cookie(client: AsyncClient) -> None:
    """Without session cookie, POST /api/states returns 401."""
    response = await client.post(
        "/api/states",
        json={"name": "Texas", "abbreviation": "TX", "is_active": True},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_state_201_happy_path(auth_client: AsyncClient) -> None:
    """Given valid body and auth, POST /api/states returns 201 and state with id."""
    response = await auth_client.post(
        "/api/states",
        json={"name": "Texas", "abbreviation": "TX", "is_active": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Texas"
    assert data["abbreviation"] == "TX"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_state_400_validation_invalid_body(auth_client: AsyncClient) -> None:
    """Invalid body (e.g. wrong type) returns 400."""
    response = await auth_client.post(
        "/api/states",
        json={"name": "X", "abbreviation": "X", "is_active": "not-a-bool"},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_state_400_conflict_duplicate_abbreviation(auth_client: AsyncClient) -> None:
    """Duplicate abbreviation returns 400 (conflict)."""
    await auth_client.post(
        "/api/states",
        json={"name": "First", "abbreviation": "XX", "is_active": True},
    )
    response = await auth_client.post(
        "/api/states",
        json={"name": "Second", "abbreviation": "XX", "is_active": True},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "already exists" in response.json()["detail"].lower() or "conflict" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_state_200_happy_path(auth_client: AsyncClient) -> None:
    """Given valid id and auth, GET /api/states/{id} returns 200 and state."""
    create = await auth_client.post(
        "/api/states",
        json={"name": "Ohio", "abbreviation": "OH", "is_active": True},
    )
    assert create.status_code == 201
    state_id = create.json()["id"]
    response = await auth_client.get(f"/api/states/{state_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == state_id
    assert data["name"] == "Ohio"
    assert data["abbreviation"] == "OH"


@pytest.mark.asyncio
async def test_get_state_401_without_cookie(client: AsyncClient) -> None:
    """Without session cookie, GET /api/states/{id} returns 401."""
    response = await client.get("/api/states/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_state_404_not_found(auth_client: AsyncClient) -> None:
    """Non-existent state id returns 404."""
    response = await auth_client.get("/api/states/999999")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_put_state_200_happy_path(auth_client: AsyncClient) -> None:
    """Given valid id, body, and auth, PUT /api/states/{id} returns 200 and updated state."""
    create = await auth_client.post(
        "/api/states",
        json={"name": "Virginia", "abbreviation": "VA", "is_active": True},
    )
    assert create.status_code == 201
    state_id = create.json()["id"]
    response = await auth_client.put(
        f"/api/states/{state_id}",
        json={"name": "Virginia (updated)", "abbreviation": "VA"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Virginia (updated)"
    assert data["abbreviation"] == "VA"


@pytest.mark.asyncio
async def test_put_state_401_without_cookie(client: AsyncClient) -> None:
    """Without session cookie, PUT /api/states/{id} returns 401."""
    response = await client.put("/api/states/1", json={"name": "X"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_state_404_not_found(auth_client: AsyncClient) -> None:
    """PUT non-existent state id returns 404."""
    response = await auth_client.put(
        "/api/states/999999",
        json={"name": "X", "abbreviation": "XX"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_state_400_conflict_duplicate_abbreviation(auth_client: AsyncClient) -> None:
    """Update state to an abbreviation that another state has returns 400."""
    await auth_client.post(
        "/api/states",
        json={"name": "State A", "abbreviation": "SA", "is_active": True},
    )
    create_b = await auth_client.post(
        "/api/states",
        json={"name": "State B", "abbreviation": "SB", "is_active": True},
    )
    assert create_b.status_code == 201
    state_b_id = create_b.json()["id"]
    response = await auth_client.put(
        f"/api/states/{state_b_id}",
        json={"abbreviation": "SA"},
    )
    assert response.status_code == 400
    assert "detail" in response.json()
