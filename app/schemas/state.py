"""State (jurisdiction) schemas — align with openapi.yaml State, StateCreate, StateUpdate."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StateBase(BaseModel):
    """Shared fields for state create/update (spec has no minLength)."""

    name: str = Field(..., max_length=255)
    abbreviation: str = Field(..., max_length=16)
    is_active: bool = True


class StateCreate(StateBase):
    """Request body for POST /api/states."""

    pass


class StateUpdate(BaseModel):
    """Request body for PUT /api/states/{state_id} — all fields optional."""

    name: str | None = Field(None, max_length=255)
    abbreviation: str | None = Field(None, max_length=16)
    is_active: bool | None = None


class StateResponse(BaseModel):
    """Response schema for state (GET one, GET list, POST, PUT) — matches openapi State."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    abbreviation: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
