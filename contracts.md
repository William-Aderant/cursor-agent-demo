# API and Data Contracts — Court Form PDF Monitor (URL Monitor)

**Version:** 3.1  
**Source of truth:** This document and `openapi.yaml` are the single source of truth for API endpoints, data models, business rules, and auth. Update whenever contracts or DB schema change.

**Reference:** PRD.md (Sections 5, 8, 10); openapi.yaml (OpenAPI 3.1)

---

## 1. Endpoints Summary

All paths are under `/api`. Auth uses HttpOnly session cookies (BFF); protected routes require a valid session unless noted.

| Group | Method | Path | Auth | Description |
|-------|--------|------|------|-------------|
| **Auth** | POST | `/api/auth/login` | No | Log in (OIDC exchange → Set-Cookie) |
| | POST | `/api/auth/logout` | Yes | Revoke session |
| | POST | `/api/auth/refresh` | Yes | Refresh session |
| | GET | `/api/auth/me` | Yes | Current user/session |
| **States** | GET | `/api/states` | Yes | List states |
| | GET | `/api/states/{state_id}` | Yes | Get state |
| | POST | `/api/states` | Yes | Create state |
| | PUT | `/api/states/{state_id}` | Yes | Update state |
| **Categories** | GET | `/api/categories` | Yes | List categories |
| | GET | `/api/categories/tree` | Yes | Category hierarchy tree |
| | GET | `/api/categories/{category_id}` | Yes | Get category |
| | GET | `/api/categories/{category_id}/children` | Yes | Child categories |
| | GET | `/api/categories/{category_id}/urls` | Yes | URLs in category |
| | POST | `/api/categories` | Yes | Create category |
| | PUT | `/api/categories/{category_id}` | Yes | Update category |
| | DELETE | `/api/categories/{category_id}` | Yes | Delete category |
| **URLs** | GET | `/api/urls` | Yes | List URLs (paginated, filters) |
| | GET | `/api/url-filters` | Yes | Filter options |
| | POST | `/api/urls` | Yes | Create URL |
| | GET | `/api/urls/{url_id}` | Yes | Get URL |
| | PUT | `/api/urls/{url_id}` | Yes | Update URL |
| | DELETE | `/api/urls/{url_id}` | Yes | Delete URL |
| | GET | `/api/urls/{url_id}/versions` | Yes | List PDF versions |
| | GET | `/api/urls/{url_id}/versions/{version_id}/pdf` | Yes | Download PDF |
| | GET | `/api/urls/{url_id}/versions/{version_id}/text` | Yes | Extracted text |
| | GET | `/api/urls/{url_id}/versions/{version_id}/preview` | Yes | PDF preview |
| | GET | `/api/urls/{url_id}/versions/{version_id}/diff-preview` | Yes | Visual diff preview |
| | GET | `/api/urls/{url_id}/versions/{version_id}/diff-info` | Yes | Diff metadata |
| | POST | `/api/urls/{url_id}/versions/{version_id}/extract-title` | Yes | Re-run title extraction |
| | GET | `/api/urls/{url_id}/similar` | Yes | Similar/relocated URLs |
| | POST | `/api/urls/bulk-delete` | Yes | Bulk delete URLs |
| | POST | `/api/urls/bulk-upload` | Yes | Bulk upload (CSV/TXT) |
| | GET | `/api/urls/upload-template` | Yes | Download upload template |
| | GET | `/api/urls/upload-guide` | Yes | Upload format guide |
| **Changes** | GET | `/api/changes` | Yes | List changes (filters) |
| | GET | `/api/changes-full` | Yes | List changes with full detail (text diffs) |
| | GET | `/api/changes/{change_id}/download` | Yes | Download changed PDF |
| | POST | `/api/changes/{change_id}/approve` | Yes | Approve change |
| | POST | `/api/changes/{change_id}/unapprove` | Yes | Revert approval |
| | POST | `/api/changes/{change_id}/intervention` | Yes | Record manual intervention |
| **Triage** | POST | `/api/triage/review/{change_id}` | Yes | Review single change |
| | POST | `/api/triage/bulk-review` | Yes | Bulk review |
| | POST | `/api/triage/override/{change_id}` | Yes | Override AI classification |
| | POST | `/api/triage/auto-approve-eligible` | Yes | Auto-approve eligible |
| | POST | `/api/triage/approve-all-pending` | Yes | Approve all pending |
| | POST | `/api/triage/dismiss-false-positives` | Yes | Dismiss false positives |
| **Monitoring** | POST | `/api/monitor/run` | Yes | Start monitoring cycle (scheduled) |
| | POST | `/api/monitor/run-now` | Yes | Run cycle immediately |
| | GET | `/api/monitor/progress` | Yes | Progress (polling) |
| | GET | `/api/monitor/progress/stream` | Yes | **SSE** real-time progress |
| | GET | `/api/status` | Yes | System status |
| **Metrics** | GET | `/api/metrics` | Yes | System metrics |
| | GET | `/api/metrics/accuracy` | Yes | Extraction accuracy |
| | GET | `/api/metrics/jurisdiction` | Yes | Per-jurisdiction metrics |
| | GET | `/api/aws-calls` | Yes | AWS API call counts |
| **Audit** | GET | `/api/audit/cycles` | Yes | List cycles |
| | GET | `/api/audit/cycles/{cycle_id}` | Yes | Cycle details |
| | GET | `/api/audit/cycles/{cycle_id}/results` | Yes | Per-URL results |
| | GET | `/api/audit/stats` | Yes | Audit statistics |
| | GET | `/api/audit/trends` | Yes | Audit trends |
| **Search** | GET | `/api/search` | Yes | Search (OpenSearch; q, state_id, category_id) |
| **Schedule** | GET | `/api/schedule` | Yes | Get schedule config |
| | PUT | `/api/schedule` | Yes | Update schedule config |
| **Legacy** | POST | `/api/kendra/index/{version_id}` | Yes | Index in Kendra (deprecated) |
| | GET | `/api/kendra/status` | Yes | Kendra status (deprecated) |

---

## 2. Data Models (DB and API)

### 2.1 Core Tables and API Shapes

- **states**  
  - DB: `id`, `name`, `abbreviation`, `is_active`, `created_at`, `updated_at`  
  - API: `State`, `StateCreate`, `StateUpdate` (see openapi.yaml).

- **categories**  
  - DB: `id`, `name`, `description`, `parent_category_id` (self-ref), `state_id`, `full_path`, `created_at`, `updated_at`  
  - API: `Category`, `CategoryCreate`, `CategoryUpdate`, `CategoryTree`.

- **monitored_urls**  
  - DB: `id`, `url`, `title`, `form_number`, `revision_date`, `state_id`, `category_id`, `is_enabled`, `last_checked`, `status`, `created_at`, `updated_at`  
  - API: `MonitoredUrl`, `MonitoredUrlCreate`, `MonitoredUrlUpdate`.  
  - Status: e.g. `active`, `inactive`, `error`, `archived`.

- **pdf_versions**  
  - DB: `id`, `url_id`, `version_number`, `pdf_hash`, `text_hash`, `normalized_hash`, `file_path`, `text_content`, `s3_raw_key`, `s3_normalized_key`, `s3_extracted_key`, `s3_text_key`, `opensearch_document_id`, `opensearch_indexed_at`, `opensearch_index_status`, `created_at`  
  - API: `PDFVersion` (and version-scoped endpoints).  
  - v3.1: S3 keys and OpenSearch fields (Kendra columns renamed).

- **change_log**  
  - DB: `id`, `url_id`, `version_id`, `change_type`, `classification`, `confidence`, `reasoning`, `status`, `reviewed_by`, `reviewed_at`, `created_at`  
  - API: `ChangeLog`, `ChangeDetail` (with url, version, text_diff).  
  - Status: `pending`, `approved`, `rejected`, `dismissed`.

- **monitoring_cycles**  
  - DB: `id`, `started_at`, `completed_at`, `total_urls`, `changes_detected`, `errors`, `status`  
  - API: `MonitoringCycle`.

- **cycle_url_results**  
  - DB: `id`, `cycle_id`, `url_id`, `status`, `change_detected`, `error_message`, `duration_ms`  
  - API: `CycleUrlResult`.

- **schedule_config**  
  - DB: `id`, `cron_expression`, `is_enabled`, `last_run`, `next_run`  
  - API: `ScheduleConfig`, `ScheduleConfigUpdate`.

### 2.2 Relationships

- State 1 → N Category  
- Category 1 → N Category (parent/children)  
- Category 1 → N MonitoredURL  
- MonitoredURL 1 → N PDFVersion  
- PDFVersion 1 → N ChangeLog  
- MonitoringCycle 1 → N CycleURLResult; CycleURLResult N → 1 MonitoredURL  

### 2.3 Pagination and Filtering

- List endpoints that support pagination use `page` (≥1) and `page_size` (1–100, default 20).  
- Response shape: `items`, `total`, `page`, `page_size` where applicable (see openapi.yaml).  
- Filter names (e.g. `state_id`, `category_id`, `status`, `is_enabled`) are stable; new query params must remain backward-compatible.

---

## 3. Business Rules

### 3.1 Auth and Sessions

- **BFF pattern:** Backend performs OIDC token exchange; no JWT in browser storage. Session is stored server-side; cookie name is configurable (e.g. `url_monitor_session`).  
- **Cookie:** HttpOnly, Secure, SameSite.  
- **Session lifecycle:** Creation (login), validation (per request), refresh, revocation (logout) are server-side only.  
- **CORS:** Allowed origins must be configured (e.g. `CORS_ALLOWED_ORIGINS`); credentials (cookies) are sent by clients.

### 3.2 States and Categories

- States are top-level org (e.g. US jurisdictions). Duplicate state abbreviation on create or update returns 400 (Bad Request).  
- Categories form a tree per state; `parent_category_id` self-reference; `full_path` maintained for hierarchy.  
- Delete category: not allowed if it has children or assigned URLs (respond with 409 or equivalent).

### 3.3 URL Management

- URL uniqueness: per state/category (or global) as defined by product; duplicate URL for same state may be rejected (400).  
- Bulk upload: CSV/TXT format as documented by `/api/urls/upload-guide` and template.  
- Bulk delete: request body contains `url_ids`; response indicates `deleted` count and any `errors`.

### 3.4 Changes and Triage

- Change status flow: `pending` → `approved` | `rejected` | `dismissed`.  
- Approve / unapprove / intervention / triage actions are idempotent where applicable (e.g. approve already approved = 200 with same state).  
- Override: triage override updates AI classification for the change; may require `classification` and optional `notes`.  
- Auto-approve eligible: only changes meeting eligibility rules (e.g. confidence threshold) are auto-approved.  
- Dismiss false positives: can accept optional `change_ids`; if omitted, behavior is defined by implementation (e.g. dismiss all eligible).

### 3.5 Monitoring

- Only one monitoring cycle runs at a time. Starting while one is running returns 409.  
- Progress: `GET /api/monitor/progress` for polling; `GET /api/monitor/progress/stream` for SSE. SSE must work with cookie-based auth (credentials sent).  
- Schedule: `GET/PUT /api/schedule`; cron expression and `is_enabled` control when cycles run.

### 3.6 Search and Legacy

- Search: `GET /api/search` with `q`, optional `state_id`, `category_id`, pagination. Backend uses OpenSearch (v3.1); Kendra is deprecated.  
- Kendra endpoints are deprecated; to be removed in v3.1. No new clients should depend on them.

### 3.7 PDF and Versions

- PDF download may be binary or redirect to presigned S3 URL when S3 is enabled.  
- Title extraction: re-run via `POST .../extract-title`; returns title, form_number, revision_date.  
- Similar URLs: `GET /api/urls/{url_id}/similar` returns candidates for relocation detection; relevance/similarity is implementation-defined.

---

## 4. Auth Flows

### 4.1 Login (BFF)

1. Client sends `POST /api/auth/login` with `{ "email", "password" }`.  
2. Backend exchanges credentials with OIDC provider (Cognito now, Okta target).  
3. On success: backend creates session, responds with `Set-Cookie` (HttpOnly session cookie) and optional JSON body (e.g. `SessionInfo`).  
4. On failure: 401, no cookie.

### 4.2 Subsequent Requests

1. Client sends request with `Cookie` header (browser does this automatically when same-origin or CORS with credentials).  
2. Backend validates session (e.g. from cookie); if valid, processes request; if invalid/expired, returns 401.

### 4.3 Refresh

1. Client sends `POST /api/auth/refresh` with session cookie.  
2. Backend extends/refreshes session; may send new `Set-Cookie`.  
3. 401 if session invalid or expired.

### 4.4 Logout

1. Client sends `POST /api/auth/logout` with session cookie.  
2. Backend revokes session and clears cookie (e.g. Set-Cookie with past expiry).  
3. 204 or 200 with no sensitive data.

### 4.5 Current User

- `GET /api/auth/me`: returns current session/user info (e.g. `SessionInfo`); 401 if not authenticated.

### 4.6 Configuration (Reference)

- `OIDC_PROVIDER`: e.g. `cognito` | `okta`  
- `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_CLIENT_SECRET`: OIDC provider config  
- `AUTH_SESSION_COOKIE_NAME`, `AUTH_SESSION_TTL_SECONDS`: session behavior  
- `CORS_ALLOWED_ORIGINS`: frontend origin(s) for CORS  

---

## 5. OpenAPI and Compliance

- **Spec:** `openapi.yaml` is OpenAPI 3.1 and the source of truth for path, method, request/response schemas, and security (cookieAuth).  
- **Implementation:** Must match the spec. If behavior and spec diverge, fix the implementation, not the spec.  
- **SSE:** `/api/monitor/progress/stream` returns `text/event-stream`; exact event schema can be documented in the spec or in this file as needed.  
- **Deprecated:** Kendra endpoints are marked deprecated in the spec and should not be used by new clients.

---

## 6. Changelog (Contracts)

| Date | Change |
|------|--------|
| 2026-02-17 | Initial contracts.md and openapi.yaml 3.1 from PRD v3.2 (Phase 1: Contracts). Auth (login, logout, refresh, me), states, categories, URLs, changes, triage, monitoring, metrics, audit, search, schedule, legacy Kendra. Data models and relationships aligned with Section 8; auth flows with Epic 2 BFF. |
| 2026-02-17 | Phase 6–7: States API implementation and integration tests. contracts: state duplicate-abbreviation → 400; openapi: add 400 for PUT /states/{state_id}. Integration tests in tests/integration (pytest-asyncio, httpx, transactional DB isolation). CI workflow added. |
