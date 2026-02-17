"""FastAPI app — mount routers at /api."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError

from app.routers.states import router as states_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Lifespan: startup/shutdown (e.g. connect/disconnect DB pools)."""
    yield


def _validation_error_detail(exc: RequestValidationError | PydanticValidationError) -> list[dict] | str:
    """Format validation errors for 400 response (spec documents 400, not 422)."""
    try:
        errors = getattr(exc, "errors", None) or []
        if not errors:
            return getattr(exc, "json", lambda: str(exc))() if hasattr(exc, "json") else str(exc)
        return [{"loc": e.get("loc"), "msg": e.get("msg")} for e in errors]
    except Exception:
        return str(exc)


async def _request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 400 for validation errors so responses match spec (201, 400)."""
    return JSONResponse(
        status_code=400,
        content={"detail": _validation_error_detail(exc)},
    )


async def _pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Return 400 for Pydantic validation errors (e.g. body type mismatch)."""
    return JSONResponse(
        status_code=400,
        content={"detail": _validation_error_detail(exc)},
    )


app = FastAPI(
    title="Court Form PDF Monitor (URL Monitor) API",
    version="3.1.0",
    lifespan=lifespan,
)

async def _integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Return 400 for DB constraint violations (e.g. duplicate abbreviation)."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Conflict: duplicate or invalid value"},
    )


app.add_exception_handler(RequestValidationError, _request_validation_exception_handler)
app.add_exception_handler(PydanticValidationError, _pydantic_validation_exception_handler)
app.add_exception_handler(IntegrityError, _integrity_error_handler)
app.include_router(states_router, prefix="/api")
