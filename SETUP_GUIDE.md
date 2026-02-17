# Agent Setup & Usage Guide

This guide walks you through setting up your environment and using the Cursor agent effectively.

---

## Step 1: Collect Required Credentials

Before you can use the agent, you need to gather credentials for the three MCP servers. Here's how to get each one:

### 1. GitHub Token (for GitHub MCP)

**Purpose**: Allows the agent to create PRs, fetch CI logs, and read repository information.

**How to get it**:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it: `Cursor Agent - [Project Name]`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (if you want CI log access)
5. Click "Generate token"
6. **Copy the token immediately** — you won't see it again!

**Add to `.env`**:
```bash
GITHUB_TOKEN=ghp_your_token_here
```

---

### 2. Apidog Credentials (for Apidog MCP)

**Purpose**: Provides live access to your API spec — endpoint definitions, Pydantic schemas, auth patterns.

**How to get it** (see **[docs/APIDOG_SETUP.md](docs/APIDOG_SETUP.md)** for full steps):

1. Sign up/login at [apidog.com](https://apidog.com)
2. **API Access Token**: Click your avatar (top-right) → **Account Settings** → **API Access Token** → create a new token and copy it (shown only once).
3. **Project ID**: Open your project → **Project Settings** (left sidebar) → **Basic Settings** → copy **Project ID**.

**Add to `.env`**:
```bash
APIDOG_PROJECT_ID=your_project_id_here
APIDOG_ACCESS_TOKEN=your_access_token_here
```

**Note**: Apidog is optional. The agent works without it; you’ll just miss live spec integration. For step-by-step setup and troubleshooting, use **[docs/APIDOG_SETUP.md](docs/APIDOG_SETUP.md)**.

---

### 3. PostgreSQL Connection String (for Postgres MCP)

**Purpose**: Allows the agent to inspect your database schema, verify migrations, and run queries.

**How to get it**:
1. **If you have a local Postgres**:
   ```bash
   # Format: postgresql://username:password@host:port/database
   DEV_DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb
   ```

2. **If you need to set up local Postgres**:
   ```bash
   # macOS (using Homebrew)
   brew install postgresql@15
   brew services start postgresql@15
   createdb mydb
   
   # Then use:
   DEV_DATABASE_URL=postgresql://$(whoami)@localhost:5432/mydb
   ```

3. **If using a cloud database** (Supabase, Neon, Railway, etc.):
   - Copy the connection string from your provider's dashboard
   - Format: `postgresql://user:password@host:port/database`

**Add to `.env`**:
```bash
DEV_DATABASE_URL=postgresql://user:password@localhost:5432/mydb
```

**Security Note**: Never commit `.env` to git. It's already in `.gitignore`.

---

## Step 2: Create Your `.env` File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your credentials:
   ```bash
   # GitHub MCP — personal access token with repo scope
   GITHUB_TOKEN=ghp_your_token_here
   
   # Apidog MCP — project ID and access token from apidog.com
   APIDOG_PROJECT_ID=your_project_id_here
   APIDOG_ACCESS_TOKEN=your_access_token_here
   
   # Postgres MCP — connection string for your dev database
   DEV_DATABASE_URL=postgresql://user:password@localhost:5432/mydb
   ```

3. Save the file.

---

## Step 3: Verify MCP Servers Are Working

After setting up `.env`, restart Cursor to load the MCP servers. Then test them:

**Test GitHub MCP**:
- Ask the agent: "Can you list the branches in this repository?"
- If it works, you'll see branch names.

**Test Postgres MCP**:
- Ask the agent: "Can you show me the tables in the database?"
- If it works, you'll see table names (or an empty list if no tables yet).

**Test Apidog MCP**:
- Ask the agent: "Can you fetch the API spec from Apidog?"
- If it works, you'll see your API endpoints.

---

## Step 4: Using the Agent Workflow

The agent follows a **7-phase workflow**. Here's how to use it:

### Phase 1: Contracts First (Start Here!)

**What you need**: A Product Requirements Document (PRD) or user stories describing your API.

**How to use**:
1. Create a document (e.g., `PRD.md`) describing:
   - What endpoints you need
   - What data they accept/return
   - Authentication requirements
   - Business rules

2. **Prompt the agent**:
   ```
   I'm starting Phase 1: Contracts. Please read PRD.md and generate:
   1. An OpenAPI 3.1 spec (openapi.yaml) covering all endpoints
   2. A contracts.md file with endpoints, data models, business rules, and auth flows
   
   Do NOT write any Python code yet — just the spec and contracts.
   ```

3. **Review the output**:
   - Check `openapi.yaml` — are all endpoints covered?
   - Check `contracts.md` — are business rules clear?
   - Make corrections if needed.

---

### Phase 2: Architecture Plan

**Prompt the agent**:
```
I'm in Phase 2: Plan. Based on openapi.yaml and contracts.md, create:
1. A docs/plan.md with the FastAPI folder structure
2. SQLAlchemy models (tables, columns, relationships, indexes)
3. Alembic migration sequence
4. Pydantic schemas needed
5. Auth strategy
6. Test file locations

Do NOT write implementation code — just the plan.
```

**Review**: Approve the architecture before proceeding.

---

### Phase 3: Database Schema

**Prompt the agent**:
```
I'm in Phase 3: Schema. Based on docs/plan.md:
1. Create SQLAlchemy models in app/models/
2. Generate Alembic migration: alembic revision --autogenerate -m "init"
3. Review the migration SQL
4. Apply it: alembic upgrade head
5. Use Postgres MCP to verify the schema matches the plan
6. Create alembic/seed.py with test data

Commit after verifying the schema.
```

**Review**: Confirm the database schema matches your plan.

---

### Phase 4: Build Endpoints

**Prompt the agent** (one endpoint group at a time):
```
I'm in Phase 4: Build. For the /orders endpoint group:
1. Create Pydantic schemas in app/schemas/ (OrderCreate, OrderResponse, OrderUpdate)
2. Create repository in app/repositories/ (async SQLAlchemy queries)
3. Create service in app/services/ (business logic)
4. Create router in app/routers/ (FastAPI endpoints)
5. Create unit tests in tests/unit/

Follow the build order: schemas → repository → service → router → tests.
```

**Review**: Check each layer before moving to the next endpoint group.

---

### Phase 5: Contract Verification

**Prompt the agent**:
```
I'm in Phase 5: Contract Verification. 
1. Start the dev server: uvicorn app.main:app --reload
2. Install schemathesis: pip install schemathesis
3. Run contract tests: schemathesis run openapi.yaml --base-url http://localhost:8000 --checks all
4. Fix any mismatches in the implementation (never modify the spec)
5. Re-run until 0 failures
```

**Review**: Confirm zero contract violations.

---

### Phase 6: Integration Tests

**Prompt the agent**:
```
I'm in Phase 6: Integration Tests. Based on contracts.md:
1. Generate integration tests in tests/integration/
2. Use pytest-asyncio and httpx.AsyncClient
3. Wrap tests in async DB transactions for isolation
4. Cover happy path, 401, 400/422, 404, 409
5. Run: pytest tests/integration -v
```

**Review**: Confirm all tests pass.

---

### Phase 7: Ship

**Prompt the agent**:
```
I'm in Phase 7: Ship.
1. Update contracts.md and openapi.yaml if anything changed
2. Open a PR via GitHub MCP with description
3. Monitor CI and fix any failures
```

**Review**: Security review — check JWT secrets, async usage, N+1 queries, CORS.

---

## Best Practices for Using the Agent

### ✅ Do:
- **Be specific**: "Create a POST /orders endpoint" is better than "add orders"
- **One thing at a time**: Build one endpoint group per session
- **Review before proceeding**: Check each phase output before moving forward
- **Use Plan Mode**: For Phases 1-2, explicitly ask for "Plan Mode" (no code)
- **Reference files**: "Based on contracts.md, create..." helps the agent stay aligned

### ❌ Don't:
- **Skip phases**: Don't jump to Phase 4 without doing Phases 1-3 first
- **Modify the spec**: If tests fail, fix the implementation, not `openapi.yaml`
- **Commit broken code**: Only commit after tests pass
- **Mix concerns**: Don't ask for auth + endpoints + tests all at once

---

## Troubleshooting

### MCP servers not working?
- Restart Cursor after creating `.env`
- Check `.env` file has correct format (no quotes around values)
- Verify credentials are valid

### Agent not following rules?
- Check `.cursor/rules/base.mdc` is present
- Explicitly reference the rule: "Following base.mdc, create..."

### Tests failing?
- Ask the agent: "Why are tests failing? Show me the error output"
- The agent can self-heal up to 3 retries

### Database connection issues?
- Verify `DEV_DATABASE_URL` format is correct
- Test connection: `psql $DEV_DATABASE_URL`
- Check Postgres is running: `brew services list` (macOS)

---

## Quick Start Checklist

- [ ] Collect GitHub token
- [ ] Collect Apidog credentials (optional)
- [ ] Set up Postgres database
- [ ] Create `.env` file with all credentials
- [ ] Restart Cursor
- [ ] Test MCP servers work
- [ ] Write PRD document
- [ ] Start Phase 1: Contracts

---

## Next Steps

Once you've completed the setup:
1. Write your PRD (Product Requirements Document)
2. Start Phase 1 by asking the agent to generate `openapi.yaml` and `contracts.md`
3. Follow the 7-phase workflow

**Ready to start?** Create your PRD and prompt the agent: "I'm starting Phase 1: Contracts. Please read [PRD.md] and generate the OpenAPI spec and contracts.md file."
