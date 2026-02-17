# FastAPI Backend Agentic Workflow — 7-Phase Reference

A contract-first pipeline for building FastAPI services with Cursor AI agents.
Each phase has a specific mode, explicit inputs/outputs, and a human approval gate.

---

## Phase 0: One-Time Setup

**Mode**: Config
**What**: Install MCP servers (Apidog, Postgres, GitHub), create `.cursor/rules/`, customize FastAPI-specific rules.
**Your action**: One-time per project. Reuse forever.

### MCP Stack

| Server | Purpose |
|--------|---------|
| Apidog / OpenAPI MCP | Live access to API spec — endpoint definitions, Pydantic schemas, auth patterns |
| Postgres MCP | Inspect live schema, run queries, verify Alembic migrations, check indexes |
| GitHub MCP | Open PRs, fetch CI logs, read pytest failures |
| Terminal (built-in) | Run pytest, alembic, ruff, mypy, httpx/curl checks |

---

## Phase 1: Contracts First — PRD to OpenAPI Spec

**Mode**: Plan Mode (no code)
**Input**: PRD document
**Output**: `api/openapi.yaml` + `contracts.md`

**Prompt the agent to**:
- Read the PRD
- Generate a valid OpenAPI 3.1 spec covering all endpoints from user stories
- For each endpoint: path, method, request body with JSON Schema (Pydantic-compatible), success response (200/201), all error responses (400, 401, 403, 404, 409, 422, 500) with detail field, security requirements (JWT bearer)
- Generate `contracts.md` — human-readable summary of endpoints, Pydantic models needed, business rules, auth flows, edge cases
- Do NOT write any Python code

**Your action**: Review the spec thoroughly. Check: all user stories covered? Error schemas explicit? Auth modeled correctly? FastAPI validates responses against this spec at runtime.

---

## Phase 2: Plan — Architecture and File Structure

**Mode**: Plan Mode (no code)
**Input**: `openapi.yaml`, `contracts.md`, cursor rules
**Output**: `docs/plan.md`

**Prompt the agent to**:
- Create an implementation plan: FastAPI folder structure (routers, services, repositories, models, schemas, core)
- SQLAlchemy models: every table, column, type (using SQLAlchemy 2.0 `mapped_column`), relationships, indexes
- Alembic migration sequence with dependencies
- Pydantic schemas derived from OpenAPI (OrderCreate, OrderResponse, OrderUpdate per endpoint)
- Auth strategy: JWT via python-jose, fastapi-users, or custom
- Dependency injection setup (get_db, get_current_user)
- Test file locations and DB isolation strategy (async transactions)
- No implementation code

**Your action**: Approve the plan, add constraints, commit.

---

## Phase 3: Schema and Migrations — Database First

**Mode**: Agent Mode
**Input**: `plan.md`, `db.mdc` rules
**Output**: SQLAlchemy models, Alembic migrations, seed script, verified schema

**Prompt the agent to**:
1. Create SQLAlchemy models in `app/models/` per the plan using SQLAlchemy 2.0 style (mapped columns, relationships, indexes)
2. Generate migration: `alembic revision --autogenerate -m "init"`
3. Review generated migration SQL — Alembic is smart but not perfect
4. Apply: `alembic upgrade head`
5. Use Postgres MCP to verify schema against the plan (query `information_schema`)
6. Create `alembic/seed.py` with test data covering all relationships
7. Commit before touching application code

**Your action**: Confirm schema matches plan. This is the second-hardest thing to fix later.

---

## Phase 4: Build — Routes, Services, Pydantic Validation

**Mode**: Agent Mode
**Input**: `plan.md`, `openapi.yaml`, `api.mdc`, `testing.mdc` rules
**Output**: Implementation files + unit tests

**Build order per endpoint**:
1. Pydantic schemas (`app/schemas/`) — OrderCreate, OrderResponse, OrderUpdate derived from OpenAPI
2. Repository (`app/repositories/`) — async SQLAlchemy queries, no business logic
3. Service (`app/services/`) — business logic, validation, calls repository
4. Router (`app/routers/`) — @router.post with response_model, depends on get_db and get_current_user
5. Unit tests (`tests/unit/`) — mock repository, test service logic

**Important**: All routes must be `async def`, all DB operations use `AsyncSession`, all HTTP clients use `httpx.AsyncClient`.

**Your action**: Review diffs per layer. Accept or redirect. Do NOT add auth yet — that's a separate pass.

---

## Phase 5: Contract Verification

**Mode**: Agent Mode
**Input**: Running dev server (`uvicorn app.main:app`), `openapi.yaml`
**Output**: Zero contract violations

**Prompt the agent to**:
1. Install schemathesis: `pip install schemathesis`
2. Run contract tests: `schemathesis run api/openapi.yaml --base-url http://localhost:8000 --checks all --hypothesis-max-examples=50`
3. For failures: identify root cause (Pydantic schema, status code, missing field, HTTPException detail)
4. Fix the implementation — NEVER modify the spec to match bad behaviour
5. Re-run until 0 failures
6. Create `tests/contract/test_openapi_compliance.py` with schemathesis.from_pytest_fixture for CI

**Your action**: Confirm zero contract violations before proceeding.

---

## Phase 6: Integration Tests — Full TDD Loop

**Mode**: Agent Mode
**Input**: `contracts.md`, `testing.mdc` rules
**Output**: Passing integration test suite

**Prompt the agent to**:
- Generate integration tests in `tests/integration/test_*.py`
- Use `pytest-asyncio` for async tests
- Use `httpx.AsyncClient` to hit FastAPI app
- Wrap each test in async DB transaction (rollback after test for isolation)
- Use factory_boy or manual factories for test data
- For every acceptance criterion: HTTP request, assert status code, response body validates against Pydantic schema, DB state correct via SQLAlchemy query
- Cover: happy path, 401, 400/422, 404, 409
- Test names match acceptance criteria exactly
- Run: `pytest tests/integration -v`

**Your action**: Confirm all tests pass. Self-healing loop handles up to 3 retries.

---

## Phase 7: Ship — PR, CI, Review

**Mode**: Agent Mode + GitHub MCP
**Input**: All passing tests, updated `contracts.md`
**Output**: Merged PR

**Prompt the agent to**:
1. Update `contracts.md` and `openapi.yaml` if implementation changed any shapes
2. FastAPI can auto-generate updated OpenAPI: `python -m app.main --export-openapi > openapi.json`
3. Open PR via GitHub MCP with description linking to contracts and listing changed endpoints
4. Monitor CI — if it fails, fetch logs and self-heal
5. CI should run: `pytest + mypy + ruff + schemathesis`
6. Flag auth and performance issues for human review

**Your action**: Human review for: JWT secret not hardcoded, async/await used correctly, N+1 queries avoided, rate limiting, CORS config, Pydantic validators for sensitive fields. Never skip the security review.

---

## Quick Reference

| Phase | Mode | Agent does | You do |
|-------|------|-----------|--------|
| 0 Setup | Config | MCP + rules installed | One-time |
| 1 Contracts | Plan | PRD -> spec + contracts.md | Review spec |
| 2 Plan | Plan | Spec -> architecture plan | Approve plan |
| 3 Schema | Agent | SQLAlchemy models -> Alembic -> verify | Confirm schema |
| 4 Build | Agent | Pydantic -> Repo -> Service -> Router + tests | Review diffs |
| 5 Contract | Agent | Schemathesis -> fix mismatches | Confirm 0 violations |
| 6 Tests | Agent | Integration tests -> self-heal | Confirm passing |
| 7 Ship | Agent + GitHub | PR + CI + update contracts | Security review |

## FastAPI-Specific Tips

- **Async all the way down**: All routes `async def`, all DB `AsyncSession`, all HTTP `httpx.AsyncClient`
- **Dependency injection**: Use `Depends()` for DB sessions and auth — makes testing trivial
- **Pydantic schemas**: Generate from OpenAPI spec, use `response_model` in route decorators
- **pytest-asyncio**: Mandatory for all tests — use `@pytest.mark.asyncio` and `httpx.AsyncClient`
