# Apidog MCP Setup Guide

This guide walks you through setting up Apidog so the Cursor agent can read your API specifications and use them for code generation, DTO updates, and documentation.

## What you need

- **Node.js 18+** (for `npx`; check with `node -v`)
- An **Apidog account** (free at [apidog.com](https://apidog.com))
- **Two values** to put in your `.env`: API Access Token and Project ID

---

## Step 1: Create an Apidog account (if you don’t have one)

1. Go to [https://apidog.com](https://apidog.com).
2. Sign up (email or SSO).
3. Create or join a team when prompted.

---

## Step 2: Get your API Access Token

The token lets the MCP server read your API specs with your account permissions.

1. In Apidog, click your **avatar** (top-right).
2. Go to **Account Settings** → **API Access Token**.
3. Click **Create a new personal token** (or **New**).
4. Give it a name (e.g. `Cursor Agent - cursor-agent-demo`).
5. Choose a validity period.
6. Click **Save and generate token**.
7. **Copy the token immediately** — it’s shown only once.

Add it to your project `.env`:

```bash
APIDOG_ACCESS_TOKEN=your_token_here
```

Keep this token secret; don’t commit it to git (`.env` is in `.gitignore`).

---

## Step 3: Get your Project ID

You need an Apidog project that contains your API spec. It can be empty at first; you can add APIs later.

1. In Apidog, **open the project** you want the agent to use (or create one).
2. In the **left sidebar**, open **Project Settings** (gear or “Settings”).
3. Open **Basic Settings**.
4. Find **Project ID** and copy it (e.g. a number like `123456`).

Add it to your project `.env`:

```bash
APIDOG_PROJECT_ID=your_project_id_here
```

---

## Step 4: Add both to `.env`

Your `.env` in the repo root should include:

```bash
# Apidog MCP
APIDOG_PROJECT_ID=your_project_id_here
APIDOG_ACCESS_TOKEN=your_token_here
```

Replace the placeholders with the values from Steps 2 and 3.

---

## Step 5: Restart Cursor

1. Save `.env`.
2. Fully quit and reopen Cursor (or reload the window) so it picks up the new env and MCP config.

---

## Step 6: Verify the connection

In Cursor (Agent mode), ask:

```text
Please fetch the API specification via MCP and tell me how many endpoints exist in the project.
```

If the agent returns info from your Apidog project (e.g. endpoint count or list), the setup is working.

Other things you can try:

- “Use MCP to fetch the API spec and list all endpoints.”
- “Based on the API specification from Apidog, generate a Pydantic schema for the Product model.”

---

## Optional: Use a local or URL OpenAPI file instead

If you don’t want to use an Apidog project, you can point the MCP server at an OpenAPI/Swagger file:

- **Remove** the `--project-id=...` argument from the Apidog server in `.cursor/mcp.json`.
- **Add** `--oas=<path-or-url>`, for example:
  - `--oas=https://petstore.swagger.io/v2/swagger.json`
  - `--oas=./openapi.yaml`

In that case you don’t need `APIDOG_PROJECT_ID` or `APIDOG_ACCESS_TOKEN` for that server.

---

## Troubleshooting

### “Cannot connect” or no API data

- Confirm **Node.js 18+**: `node -v`
- Confirm **`.env`** has `APIDOG_PROJECT_ID` and `APIDOG_ACCESS_TOKEN` (no typos, no extra spaces).
- **Restart Cursor** after changing `.env`.
- In Apidog, confirm the project has at least one API; an empty project can sometimes return no data.

### Token invalid or expired

- In Apidog: **Account Settings** → **API Access Token**.
- Create a new token and update `APIDOG_ACCESS_TOKEN` in `.env`, then restart Cursor.

### Project ID wrong

- In Apidog: **Project Settings** → **Basic Settings** → copy **Project ID** again.
- Update `APIDOG_PROJECT_ID` in `.env` and restart Cursor.

### Caching / stale spec

The MCP server caches the spec. If you change the API in Apidog, ask the agent to refresh, for example:

```text
Please reload the API specification and then [your task].
```

---

## References

- [Apidog MCP Server (official docs)](https://docs.apidog.com/apidog-mcp-server)
- [Connect Apidog project to AI](https://docs.apidog.com/connect-apidog-project-to-ai-901476m0)
- [API Access Token](https://docs.apidog.com/api-access-token)
- [apidog-mcp-server on npm](https://www.npmjs.com/package/apidog-mcp-server)
