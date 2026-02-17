# FastAPI Backend Agentic Workflow Scaffold

A reusable starting point for building FastAPI services with Cursor AI agents. Provides the Phase 0 infrastructure — MCP configs, Cursor rules, and templates — so you can jump straight into Phase 1 (Contracts) on any new FastAPI project.

## Stack

- **Framework**: FastAPI
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Testing**: pytest + pytest-asyncio + httpx + Schemathesis
- **Code Quality**: Black (formatting), Ruff (linting), mypy (type checking)

## What's Included

```
.cursor/
  mcp.json                # Apidog, Postgres, and GitHub MCP servers
  rules/
    base.mdc              # Always-on: FastAPI project conventions, agentic workflow rules
    api.mdc               # Auto-attached: FastAPI routers, Pydantic schemas, async patterns
    db.mdc                # Auto-attached: SQLAlchemy 2.0, Alembic migrations
    testing.mdc            # Auto-attached: pytest, pytest-asyncio, httpx.AsyncClient
docs/
  workflow.md             # 7-phase workflow reference
contracts.md              # Template — single source of truth for API contracts
.env.example              # Required environment variables
```

## Getting Started

1. **Copy this scaffold** into your new FastAPI project directory
2. **Set up Python environment**: `poetry install` or `pip install -r requirements.txt`
3. **Set up local database** (if needed):
   - PostgreSQL is already installed and configured for this demo
   - Database name: `cursor_agent_demo`
   - Use `./scripts/db.sh` to manage the database (start, stop, connect, reset)
   - Connection string is already in `.env`
4. **Create `.env`** from `.env.example` and add your tokens/credentials (GitHub token, Apidog if using)
5. **Start Phase 1** — give the agent your PRD and ask it to generate `openapi.yaml` + `contracts.md`

### Local Database Management

A local PostgreSQL database (`cursor_agent_demo`) has been set up for this demo. Use the helper script:

```bash
# Start/stop PostgreSQL service
./scripts/db.sh start
./scripts/db.sh stop

# Connect to the database
./scripts/db.sh connect

# Reset the database (⚠️ drops all data)
./scripts/db.sh reset

# Show connection string
./scripts/db.sh url
```

The connection string is configured in `.env` as `DEV_DATABASE_URL`.

## The 7-Phase Workflow

| Phase | Mode | What Happens |
|-------|------|-------------|
| 0 Setup | Config | MCP servers + rules (this scaffold) |
| 1 Contracts | Plan | PRD -> OpenAPI spec + contracts.md |
| 2 Plan | Plan | Spec -> architecture plan + SQLAlchemy models |
| 3 Schema | Agent | SQLAlchemy models -> Alembic migrations -> Postgres MCP verification |
| 4 Build | Agent | Pydantic schemas -> Repository -> Service -> Router + tests |
| 5 Contract | Agent | Schemathesis vs spec -> self-heal mismatches |
| 6 Tests | Agent | Integration tests from acceptance criteria -> self-heal |
| 7 Ship | Agent | Update contracts, open PR, monitor CI |

See [docs/workflow.md](docs/workflow.md) for the full reference with prompts.

## MCP Servers

| Server | Package | Purpose |
|--------|---------|---------|
| Apidog | `apidog-mcp-server` | Live API spec access — endpoint definitions, Pydantic schemas, auth |
| Postgres | `@modelcontextprotocol/server-postgres` | Schema inspection, query verification, migration checks |
| GitHub | `@modelcontextprotocol/server-github` | PR creation, CI log fetching, review automation |

## Key Principles

- **Contract-first**: define the API spec before writing any implementation
- **contracts.md is the anchor**: every agent reads it before changes, updates it after
- **Fix the implementation, not the spec**: when tests fail, the spec is the requirement
- **One endpoint group per session**: small scope = clean diffs, easier reviews
- **Schema is the backbone**: verify via Postgres MCP after every migration, commit before application code
- **Async all the way down**: all routes `async def`, all DB `AsyncSession`, all HTTP `httpx.AsyncClient`

## FastAPI-Specific Notes

- FastAPI auto-generates OpenAPI from code (`app.openapi()`), but spec-first is cleaner for agentic workflows
- Use dependency injection (`Depends()`) for DB sessions and auth — makes testing trivial
- All integration tests must use `pytest-asyncio` and `httpx.AsyncClient` — never sync `TestClient`
- Alembic autogenerate is smart but review migrations before applying — verify via Postgres MCP
