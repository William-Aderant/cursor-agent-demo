"""States API — GET list, GET one, POST create, PUT update. Paths under /api (see main.py)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_state_service, require_session_cookie
from app.schemas.state import StateCreate, StateResponse, StateUpdate
from app.services.state_service import (
    StateConflictError,
    StateNotFoundError,
    StateService,
)

router = APIRouter(prefix="/states", tags=["States"], dependencies=[Depends(require_session_cookie)])


@router.get("", response_model=list[StateResponse])
async def list_states(
    service: Annotated[StateService, Depends(get_state_service)],
) -> list[StateResponse]:
    """List all states/jurisdictions."""
    return await service.list_states()


@router.get("/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: int,
    service: Annotated[StateService, Depends(get_state_service)],
) -> StateResponse:
    """Get state details."""
    try:
        return await service.get_state(state_id)
    except StateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("", response_model=StateResponse, status_code=status.HTTP_201_CREATED)
async def create_state(
    body: StateCreate,
    service: Annotated[StateService, Depends(get_state_service)],
) -> StateResponse:
    """Create a new state."""
    try:
        return await service.create_state(body)
    except StateConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.put("/{state_id}", response_model=StateResponse)
async def update_state(
    state_id: int,
    body: StateUpdate,
    service: Annotated[StateService, Depends(get_state_service)],
) -> StateResponse:
    """Update state."""
    try:
        return await service.update_state(state_id, body)
    except StateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except StateConflictError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
