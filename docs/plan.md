# Phase 2: Implementation Plan — Court Form PDF Monitor API

**Version:** 3.1  
**Based on:** openapi.yaml, contracts.md, .cursor/rules/base.mdc  
**Scope:** Plan only — no implementation code. Defines folder structure, SQLAlchemy models, migrations, Pydantic schemas, auth strategy, and test layout.

---

## 1. FastAPI Folder Structure

```
app/
  __init__.py
  main.py                    # FastAPI app, lifespan, middleware, mount routers at /api
  routers/
    __init__.py
    auth.py                   # POST /auth/login, /auth/logout, /auth/refresh, GET /auth/me
    states.py                 # /states, /states/{state_id}
    categories.py             # /categories, /categories/tree, /categories/{id}, .../children, .../urls
    urls.py                   # /urls, /url-filters, /urls/{id}, .../versions, .../similar, bulk-*, upload-*
    changes.py                # /changes, /changes-full, /changes/{id}/download, approve, unapprove, intervention
    triage.py                 # /triage/review/{id}, bulk-review, override, auto-approve-eligible, approve-all-pending, dismiss-false-positives
    monitor.py                # /monitor/run, run-now, progress, progress/stream (SSE), /status
    metrics.py                # /metrics, /metrics/accuracy, /metrics/jurisdiction, /aws-calls
    audit.py                  # /audit/cycles, /audit/cycles/{id}, .../results, /audit/stats, /audit/trends
    search.py                 # GET /search
    schedule.py               # GET/PUT /schedule
    kendra.py                 # Legacy: /kendra/index/{version_id}, /kendra/status (deprecated)
  services/
    __init__.py
    auth_service.py           # OIDC exchange, session create/validate/refresh/revoke
    state_service.py
    category_service.py
    url_service.py
    change_service.py
    triage_service.py
    monitor_service.py
    metrics_service.py
    audit_service.py
    search_service.py
    schedule_service.py
  repositories/
    __init__.py
    state_repository.py
    category_repository.py
    url_repository.py
    pdf_version_repository.py
    change_repository.py
    cycle_repository.py
    schedule_repository.py
    session_repository.py     # Server-side session store (BFF)
  models/
    __init__.py               # Export all models, Base
    base.py                   # DeclarativeBase, shared mixins (e.g. created_at/updated_at)
    state.py
    category.py
    monitored_url.py
    pdf_version.py
    change_log.py
    monitoring_cycle.py
    cycle_url_result.py
    schedule_config.py
    session.py                # BFF session row
  schemas/
    __init__.py
    common.py                 # Pagination params, ErrorDetail, generic list wrappers
    auth.py                   # LoginRequest, SessionInfo
    state.py                  # State, StateCreate, StateUpdate
    category.py               # Category, CategoryCreate, CategoryUpdate, CategoryTree
    url.py                    # MonitoredUrl, MonitoredUrlCreate, MonitoredUrlUpdate, UrlListPage, UrlFilters, SimilarUrlCandidate
    pdf_version.py            # PDFVersion
    change.py                 # ChangeLog, ChangeDetail, ChangeListPage
    monitor.py                # MonitorProgress
    audit.py                  # MonitoringCycle, CycleUrlResult
    metrics.py                # SystemMetrics
    search.py                 # SearchResultPage (items schema TBD per OpenSearch hit shape)
    schedule.py               # ScheduleConfig, ScheduleConfigUpdate
  core/
    __init__.py
    config.py                 # pydantic-settings (DB, OIDC, CORS, cookie name, TTL)
    database.py               # AsyncEngine, async_session_factory, get_db dependency
    security.py               # Session validation from cookie, cookie set/clear helpers (no JWT in browser)
    oidc/
      __init__.py
      base.py                 # Abstract OIDC adapter interface
      cognito.py              # Cognito adapter (token exchange, user info)
      okta.py                  # Okta adapter (stub/interface parity)
  dependencies.py            # get_current_user (from cookie/session), optional get_db
alembic/
  env.py                      # Async migration env, use models from app.models
  script.py.mako
  versions/
    # Migration files (see Section 3)
tests/
  conftest.py                 # Fixtures: async client, db session, test data, auth cookie
  unit/
    services/
    repositories/
    routers/                  # Routers with mocked services
  integration/
    api_*                     # Full request/response against test DB
  contract/
    test_openapi.py           # Validate responses against openapi.yaml
pyproject.toml
openapi.yaml
contracts.md
docs/
  plan.md                     # This file
```

**Mounting:** In `main.py`, include each router with prefix (e.g. `app.include_router(auth_router, prefix="/api", tags=["Auth"])`). Paths in routers are defined without `/api` so that the prefix supplies it (e.g. router path `"/auth/login"` → `/api/auth/login`).

**Health / OpenAPI:** Optional `GET /health` and `GET /openapi.json` at app level; spec states `/api/openapi.json` — either mount under `/api` or redirect so the contract is satisfied.

---

## 2. SQLAlchemy Models (Tables, Columns, Relationships, Indexes)

**Conventions:** Async SQLAlchemy 2.0 style; `Mapped[...]` and `mapped_column(...)`; `relationship(..., lazy="selectin"` or `"joined"` where appropriate to avoid N+1. All tables use integer primary key `id` (BIGINT where needed for scale). Timestamps in UTC.

### 2.1 Base and Mixins

- **Base:** `sqlalchemy.orm.DeclarativeBase`.
- **Mixin (optional):** `CreatedUpdatedMixin` with `created_at`, `updated_at` (DateTime, server default, onupdate).

### 2.2 states

| Column        | Type        | Nullable | Default | Notes |
|---------------|-------------|----------|---------|-------|
| id            | BigInteger  | No       | identity | PK |
| name          | String(255) | No       | —       | |
| abbreviation  | String(16)  | No       | —       | |
| is_active     | Boolean     | No       | True    | |
| created_at    | DateTime    | No       | now()   | UTC |
| updated_at    | DateTime    | No       | now()   | UTC, onupdate |

- **Indexes:** `ix_states_abbreviation` (unique), `ix_states_is_active`.
- **Relationships:** `categories` → one-to-many to Category.

### 2.3 categories

| Column             | Type         | Nullable | Default | Notes |
|--------------------|--------------|----------|---------|-------|
| id                 | BigInteger   | No       | identity | PK |
| name               | String(255)  | No       | —       | |
| description        | Text         | Yes      | —       | |
| parent_category_id | BigInteger   | Yes      | —       | FK → categories.id |
| state_id           | BigInteger   | No       | —       | FK → states.id |
| full_path          | String(1024) | No       | —       | Hierarchy path (e.g. /a/b/c) |
| created_at         | DateTime     | No       | now()   | UTC |
| updated_at         | DateTime     | No       | now()   | UTC |

- **Indexes:** `ix_categories_state_id`, `ix_categories_parent_category_id`, `ix_categories_full_path` (for tree queries).
- **Relationships:** `state` → many-to-one State; `parent` → self-ref many-to-one Category; `children` → one-to-many Category; `monitored_urls` → one-to-many MonitoredUrl.

### 2.4 monitored_urls

| Column        | Type          | Nullable | Default | Notes |
|---------------|---------------|----------|---------|-------|
| id            | BigInteger    | No       | identity | PK |
| url           | String(2048)  | No       | —       | |
| title         | String(512)   | Yes      | —       | |
| form_number   | String(128)   | Yes      | —       | |
| revision_date | Date          | Yes      | —       | |
| state_id      | BigInteger    | No       | —       | FK → states.id |
| category_id   | BigInteger    | Yes      | —       | FK → categories.id |
| is_enabled    | Boolean       | No       | True    | |
| last_checked  | DateTime      | Yes      | —       | UTC |
| status        | String(32)    | No       | —       | active, inactive, error, archived |
| created_at    | DateTime      | No       | now()   | UTC |
| updated_at    | DateTime      | No       | now()   | UTC |

- **Indexes:** `ix_monitored_urls_state_id`, `ix_monitored_urls_category_id`, `ix_monitored_urls_status`, `ix_monitored_urls_is_enabled`, `ix_monitored_urls_last_checked`.
- **Relationships:** `state` → State; `category` → Category; `pdf_versions` → one-to-many PDFVersion; `change_logs` → one-to-many ChangeLog (via version).

### 2.5 pdf_versions

| Column                  | Type          | Nullable | Default | Notes |
|-------------------------|---------------|----------|---------|-------|
| id                      | BigInteger    | No       | identity | PK |
| url_id                  | BigInteger    | No       | —       | FK → monitored_urls.id |
| version_number          | Integer       | No       | —       | Per-URL sequence |
| pdf_hash                | String(64)    | No       | —       | |
| text_hash               | String(64)    | Yes      | —       | |
| normalized_hash         | String(64)    | Yes      | —       | |
| file_path               | String(1024)  | Yes      | —       | Local path (legacy) |
| text_content            | Text          | Yes      | —       | Extracted text |
| s3_raw_key              | String(512)   | Yes      | —       | v3.1 S3 |
| s3_normalized_key       | String(512)   | Yes      | —       | |
| s3_extracted_key        | String(512)   | Yes      | —       | |
| s3_text_key             | String(512)   | Yes      | —       | |
| opensearch_document_id  | String(128)   | Yes      | —       | v3.1 (replaces kendra_document_id) |
| opensearch_indexed_at   | DateTime      | Yes      | —       | UTC |
| opensearch_index_status | String(32)    | Yes      | —       | |
| created_at              | DateTime      | No       | now()   | UTC |

- **Indexes:** `ix_pdf_versions_url_id`, `ix_pdf_versions_created_at`, `ix_pdf_versions_opensearch_document_id` (if lookups by doc id).
- **Unique:** `(url_id, version_number)`.
- **Relationships:** `monitored_url` → MonitoredUrl; `change_logs` → one-to-many ChangeLog.

### 2.6 change_log

| Column       | Type         | Nullable | Default | Notes |
|--------------|--------------|----------|---------|-------|
| id           | BigInteger   | No       | identity | PK |
| url_id       | BigInteger   | No       | —       | FK → monitored_urls.id |
| version_id   | BigInteger   | No       | —       | FK → pdf_versions.id |
| change_type  | String(64)   | No       | —       | |
| classification| String(128) | Yes      | —       | AI or override |
| confidence   | Float        | Yes      | —       | 0–1 |
| reasoning    | Text         | Yes      | —       | |
| status       | String(32)   | No       | —       | pending, approved, rejected, dismissed |
| reviewed_by  | String(255)  | Yes      | —       | User/session id |
| reviewed_at  | DateTime     | Yes      | —       | UTC |
| created_at   | DateTime     | No       | now()   | UTC |

- **Indexes:** `ix_change_log_url_id`, `ix_change_log_version_id`, `ix_change_log_status`, `ix_change_log_created_at`.
- **Relationships:** `monitored_url` → MonitoredUrl; `version` → PDFVersion.

### 2.7 monitoring_cycles

| Column            | Type        | Nullable | Default | Notes |
|-------------------|-------------|----------|---------|-------|
| id                | BigInteger  | No       | identity | PK |
| started_at        | DateTime    | No       | now()   | UTC |
| completed_at      | DateTime    | Yes      | —       | UTC |
| total_urls         | Integer     | No       | 0       | |
| changes_detected  | Integer     | No       | 0       | |
| errors            | Integer     | No       | 0       | |
| status            | String(32)  | No       | —       | running, completed, failed |

- **Indexes:** `ix_monitoring_cycles_status`, `ix_monitoring_cycles_started_at`.
- **Relationships:** `cycle_url_results` → one-to-many CycleUrlResult.

### 2.8 cycle_url_results

| Column          | Type        | Nullable | Default | Notes |
|-----------------|-------------|----------|---------|-------|
| id              | BigInteger  | No       | identity | PK |
| cycle_id        | BigInteger  | No       | —       | FK → monitoring_cycles.id |
| url_id          | BigInteger  | No       | —       | FK → monitored_urls.id |
| status          | String(32)  | No       | —       | |
| change_detected  | Boolean     | No       | False   | |
| error_message   | Text        | Yes      | —       | |
| duration_ms     | Integer     | Yes      | —       | |

- **Indexes:** `ix_cycle_url_results_cycle_id`, `ix_cycle_url_results_url_id`.
- **Relationships:** `cycle` → MonitoringCycle; `monitored_url` → MonitoredUrl.

### 2.9 schedule_config

| Column         | Type        | Nullable | Default | Notes |
|----------------|-------------|----------|---------|-------|
| id             | BigInteger  | No       | identity | PK |
| cron_expression| String(128) | No      | —       | |
| is_enabled     | Boolean     | No       | True    | |
| last_run       | DateTime    | Yes      | —       | UTC |
| next_run       | DateTime    | Yes      | —       | UTC |

- **Indexes:** None required (single-row or small table). Optional unique constraint if single config row.
- **Relationships:** None.

### 2.10 sessions (BFF server-side session store)

| Column    | Type        | Nullable | Default | Notes |
|-----------|-------------|----------|---------|-------|
| id        | BigInteger  | No       | identity | PK |
| token     | String(64)  | No       | —       | Opaque session token (indexed, unique) |
| user_id   | String(255) | No       | —       | OIDC sub or provider user id |
| email     | String(255) | Yes      | —       | Cached for SessionInfo |
| expires_at| DateTime    | No       | —       | UTC |
| created_at| DateTime    | No       | now()   | UTC |

- **Indexes:** `ix_sessions_token` (unique), `ix_sessions_expires_at` (for cleanup).
- **Relationships:** None. Cookie value maps to `token`; validation loads row and checks `expires_at`.

---

## 3. Alembic Migration Sequence

- **Alembic:** Async engine in `env.py`; `target_metadata` from `app.models.Base.metadata`; run migrations with `alembic upgrade head`.

| Order | Migration Id (example) | Description |
|-------|------------------------|-------------|
| 1     | `xxxx_initial_schema`  | Create all tables: states, categories, monitored_urls, pdf_versions, change_log, monitoring_cycles, cycle_url_results, schedule_config, sessions. All columns as in Section 2. Use OpenSearch naming from start (opensearch_document_id, opensearch_indexed_at, opensearch_index_status); do not create kendra_* columns. |
| 2     | (optional)            | Only if initial migration omitted S3/OpenSearch: add s3_* and opensearch_* columns to pdf_versions, or rename kendra_* → opensearch_* per contracts. For greenfield, migration 1 is sufficient. |

**Dependency order within initial migration:** states → categories (state_id) → monitored_urls (state_id, category_id) → pdf_versions (url_id) → change_log (url_id, version_id); monitoring_cycles (standalone) → cycle_url_results (cycle_id, url_id); schedule_config (standalone); sessions (standalone).

---

## 4. Pydantic Schemas (Needed)

Align with openapi.yaml component schemas. Use `from_config` / `model_config` for ORM mode where reading from DB (e.g. `from_attributes=True`). All request/response models should be in `app/schemas/`; no `Any` types.

### 4.1 common.py

- **PageParams:** `page: int = 1`, `page_size: int = 20` (1–100).
- **Paginated[T]:** Generic base with `items`, `total`, `page`, `page_size` (or separate schema per entity where shape differs).
- **ErrorDetail:** `detail: str`, `errors: list | None` (validation errors).

### 4.2 auth.py

- **LoginRequest:** `email: EmailStr`, `password: SecretStr` (or str).
- **SessionInfo:** `user_id: str | None`, `email: str | None`, `expires_at: datetime`.

### 4.3 state.py

- **State:** id, name, abbreviation, is_active, created_at, updated_at.
- **StateCreate:** name, abbreviation, is_active (default True).
- **StateUpdate:** name, abbreviation, is_active (all optional).

### 4.4 category.py

- **Category:** id, name, description, parent_category_id, state_id, full_path, created_at, updated_at.
- **CategoryCreate:** name, state_id; description, parent_category_id optional.
- **CategoryUpdate:** name, description, parent_category_id (all optional).
- **CategoryTree:** recursive structure (id, name, children: list[CategoryTree]).

### 4.5 url.py

- **MonitoredUrl:** id, url, title, form_number, revision_date, state_id, category_id, is_enabled, last_checked, status, created_at, updated_at.
- **MonitoredUrlCreate:** url, state_id; title, form_number, category_id, is_enabled optional.
- **MonitoredUrlUpdate:** url, title, form_number, state_id, category_id, is_enabled (all optional).
- **UrlListPage:** items (list[MonitoredUrl]), total, page, page_size.
- **UrlFilters:** states, statuses, categories (list structures per API).
- **SimilarUrlCandidate:** url_id, url, similarity_score, title.
- **BulkDeleteUrlsRequest:** url_ids: list[int].
- **BulkDeleteUrlsResponse:** deleted: int, errors: list[str].

### 4.6 pdf_version.py

- **PDFVersion:** id, url_id, version_number, pdf_hash, text_hash, normalized_hash, file_path, created_at, s3_raw_key, s3_normalized_key, opensearch_document_id, opensearch_indexed_at (and other version fields as in openapi).

### 4.7 change.py

- **ChangeLog:** id, url_id, version_id, change_type, classification, confidence, reasoning, status, reviewed_by, reviewed_at, created_at.
- **ChangeDetail:** ChangeLog plus url (MonitoredUrl), version (PDFVersion), text_diff (str).
- **ChangeListPage:** items (list[ChangeLog]), total, page, page_size.
- **TriageReviewRequest:** action (approve | reject | dismiss), notes optional.
- **BulkReviewRequest:** change_ids, action, notes optional.
- **OverrideRequest:** classification, notes optional.
- **InterventionRequest:** notes optional.

### 4.8 monitor.py

- **MonitorProgress:** is_running, cycle_id, current_url, total_urls, percent_complete, status, started_at.

### 4.9 audit.py

- **MonitoringCycle:** id, started_at, completed_at, total_urls, changes_detected, errors, status.
- **CycleUrlResult:** id, cycle_id, url_id, status, change_detected, error_message, duration_ms.

### 4.10 metrics.py

- **SystemMetrics:** automation_rate, success_rate, total_urls, pending_changes (and any other KPI fields from API).

### 4.11 search.py

- **SearchResultPage:** items (list of search hit schema — define per OpenSearch response shape), total, page, page_size.

### 4.12 schedule.py

- **ScheduleConfig:** id, cron_expression, is_enabled, last_run, next_run.
- **ScheduleConfigUpdate:** cron_expression, is_enabled (optional).

---

## 5. Auth Strategy

### 5.1 Overview

- **Pattern:** BFF (Backend For Frontend). Backend performs OIDC token exchange with Cognito (current) or Okta (target). No JWT stored in browser; session stored server-side; HttpOnly, Secure, SameSite cookie holds session token.
- **Cookie name:** From config (e.g. `AUTH_SESSION_COOKIE_NAME` = `url_monitor_session`). Cookie value = opaque session token (e.g. `sessions.token`).

### 5.2 Components

- **core/config.py:** `OIDC_PROVIDER`, `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_CLIENT_SECRET`, `AUTH_SESSION_COOKIE_NAME`, `AUTH_SESSION_TTL_SECONDS`, `CORS_ALLOWED_ORIGINS`.
- **core/security.py:** Helpers to set cookie (with HttpOnly, Secure, SameSite), clear cookie (logout), parse token from request cookies; no JWT encoding/decoding in browser.
- **core/oidc/base.py:** Abstract interface (e.g. `exchange_credentials(email, password) -> OIDCTokens | None`, `get_user_info(access_token) -> UserInfo | None`).
- **core/oidc/cognito.py:** Cognito implementation (token endpoint, userinfo); used when `OIDC_PROVIDER=cognito`.
- **core/oidc/okta.py:** Stub implementing same interface for Okta (swap when ready).
- **repositories/session_repository.py:** Create session (insert into `sessions`), get by token, refresh (extend expires_at), revoke (delete or mark expired).
- **services/auth_service.py:** Login: call OIDC adapter exchange → create session row → return SessionInfo and instruct response to set cookie. Logout: revoke session, clear cookie. Refresh: load session by cookie, extend TTL, optionally set new cookie. Me: load session, return SessionInfo.
- **dependencies.py:** `get_current_user`: read cookie → resolve session → return user/session context or raise 401.

### 5.3 Route Protection

- **Public (no session):** `POST /api/auth/login`. Optionally `GET /health`, `GET /api/openapi.json` if exposed.
- **Protected (session required):** All other `/api/*` routes. Use `Depends(get_current_user)` (or equivalent) on router or per-route.

### 5.4 CORS

- Allow origins from `CORS_ALLOWED_ORIGINS`; allow credentials (cookies); allow methods/headers as needed for API (GET, POST, PUT, DELETE, etc.). Configure in `main.py` middleware.

### 5.5 SSE

- `/api/monitor/progress/stream` must accept credentials (cookie). Validate session before starting stream; return 401 if invalid.

---

## 6. Test File Locations

- **tests/conftest.py:** Async client (TestClient or httpx.AsyncClient), async DB session fixture (rollback or isolated DB), fixtures for State/Category/Url/Version/ChangeLog/Cycle/Schedule/Session, helper to set auth cookie on client.
- **tests/unit/services/**  
  - `test_auth_service.py`, `test_state_service.py`, `test_category_service.py`, `test_url_service.py`, `test_change_service.py`, `test_triage_service.py`, `test_monitor_service.py`, `test_metrics_service.py`, `test_audit_service.py`, `test_search_service.py`, `test_schedule_service.py`.  
  - Services tested with mocked repositories; no real DB.
- **tests/unit/repositories/**  
  - `test_state_repository.py`, `test_category_repository.py`, `test_url_repository.py`, … (one per repository).  
  - Use real async DB (test DB or SQLite in-memory) with rollback/truncate; test CRUD and queries only.
- **tests/unit/routers/**  
  - `test_auth_router.py`, `test_states_router.py`, `test_categories_router.py`, … (routers with mocked services).  
  - Verify status codes, response shape, and dependency injection; no full integration.
- **tests/integration/**  
  - `api_auth.py`, `api_states.py`, `api_categories.py`, `api_urls.py`, `api_changes.py`, `api_triage.py`, `api_monitor.py`, `api_metrics.py`, `api_audit.py`, `api_search.py`, `api_schedule.py`, `api_sse.py` (or combined `api_*.py`).  
  - Full request/response against running app and test DB; auth via cookie fixture.
- **tests/contract/**  
  - `test_openapi.py`: For selected endpoints (or all), perform request and validate response body and status against openapi.yaml (e.g. using openapi-spec-validator or custom loader). Ensures implementation conforms to spec.

**No implementation code** — this plan is the only deliverable for Phase 2. Implementation follows in later phases.
