# Quick Start — Agent Setup

## 1. Get Your Credentials (5 minutes)

### GitHub Token
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Copy token

### API spec — OpenAPI file (no account needed)
The project uses **`openapi.yaml`** at the repo root as the source of truth. The MCP server reads this file (no Apidog account required). See [What you need to do](#what-you-need-to-do-openapi-file) below.

### PostgreSQL
- **Local**: `postgresql://username@localhost:5432/dbname`
- **Cloud**: Copy connection string from provider
- **psql on PATH (macOS)**: If `psql` isn’t found, install the client: `brew install libpq` then add to PATH: `export PATH="/opt/homebrew/opt/libpq/bin:$PATH"` (or add that line to `~/.zshrc`).

---

## 2. Create `.env` File

```bash
cp .env.example .env
```

Fill in (Apidog is not used when using the OpenAPI file):
```bash
GITHUB_TOKEN=ghp_your_token_here
DEV_DATABASE_URL=postgresql://user:pass@host:5432/db
```

---

## 3. Restart Cursor

Close and reopen Cursor to load MCP servers.

---

## 4. Test MCP Servers

Ask the agent:
- "List branches in this repo" (GitHub)
- "Show tables in the database" (Postgres)
- "Fetch API spec from the OpenAPI file" (OpenAPI MCP reads `openapi.yaml`)

---

## What you need to do: OpenAPI file

1. **Edit `openapi.yaml`** in the repo root.  
   A minimal placeholder is there already. Replace it with your real API spec (OpenAPI 3.x YAML or JSON). This file is the **source of truth** for the agent.

2. **Restart Cursor** after changing `.cursor/mcp.json` or `openapi.yaml` so the OpenAPI MCP server picks up the file.

3. **No Apidog or extra env vars** are required. You can remove `APIDOG_PROJECT_ID` and `APIDOG_ACCESS_TOKEN` from `.env` if you had them.

---

## 5. Start Development

### Phase 1: Contracts (Start Here!)
```
I'm starting Phase 1: Contracts. Read [PRD.md] and generate:
1. openapi.yaml (OpenAPI 3.1 spec)
2. contracts.md (endpoints, models, rules)

Do NOT write Python code yet.
```

### Phase 2: Plan
```
I'm in Phase 2: Plan. Based on openapi.yaml, create docs/plan.md with:
- FastAPI folder structure
- SQLAlchemy models
- Alembic migration plan
- Pydantic schemas
- Auth strategy

No implementation code.
```

### Phase 3: Schema
```
I'm in Phase 3: Schema. Create SQLAlchemy models, generate Alembic migration,
apply it, and verify via Postgres MCP.
```

### Phase 4: Build (One endpoint group at a time)
```
I'm in Phase 4: Build. For /orders endpoints:
1. Pydantic schemas
2. Repository (async queries)
3. Service (business logic)
4. Router (FastAPI endpoints)
5. Unit tests
```

### Phase 5: Contract Verification
```
I'm in Phase 5: Contract Verification. Run schemathesis against the running
server and fix any mismatches.
```

### Phase 6: Integration Tests
```
I'm in Phase 6: Integration Tests. Generate integration tests covering all
acceptance criteria from contracts.md.
```

### Phase 7: Ship
```
I'm in Phase 7: Ship. Update contracts.md, open PR via GitHub MCP, monitor CI.
```

---

## Key Rules

✅ **Do**:
- One endpoint group per session
- Review each phase before proceeding
- Fix implementation, not the spec
- Commit after tests pass

❌ **Don't**:
- Skip phases
- Modify `openapi.yaml` to match bad code
- Mix multiple concerns in one request

---

## Need Help?

- Full guide: See `SETUP_GUIDE.md`
- Workflow details: See `docs/workflow.md`
- Rules: See `.cursor/rules/base.mdc`
