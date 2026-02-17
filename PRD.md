# v3.2 - Court Form PDF Monitor (URL Monitor) — Backend PRD

# Court Form PDF Monitor (URL Monitor) — Backend Product Requirements Document

**Version:** 3.2

**Date:** 2026-02-17

**Status:** Active Development

**Repository:** [aderant/coe-services/url-monitor](https://github.com/aderant/coe-services/tree/main/url-monitor)

**Scope:** Backend only (API, services, data, infrastructure). Frontend and UI are out of scope for this document.

**Audience:** Backend engineers, API maintainers, DevOps/infrastructure, product stakeholders, AWS Solutions Architects

---

> **Canonical Precedence:** This document is the single source of truth for the URL Monitor project.
If any companion document, change log, or prior PRD version conflicts with this document, the
language in this file takes precedence. All team members should reference this document for
architectural decisions, technology choices, and delivery priorities.
> 

---

## How to Read This Document

This PRD is organized to support two reading modes:

1. **Top-down (recommended for first read):** Start at Section 0 (Execution Priority), then proceed through each section in order. This gives you the full picture of what we are building, why, and how.
2. **Reference lookup:** Use the table of contents below to jump directly to the section relevant to your current task. Each epic (Section 6) is self-contained with its own context, user stories, acceptance criteria, and implementation notes.

**Key conventions:**
- Acceptance criteria use checkbox format (`[ ]`) — these become the definition of “done” for each deliverable.
- Owner roles are generic (e.g., “Backend Lead”) rather than individual names, so assignments can flex as the team evolves.
- Sections marked **(Locked)** contain decisions that have been finalized and must not be changed without a full team review.
- Sections marked **(Future)** are scoped for v3.2+ and are included for context only — they are not part of the v3.1 delivery commitment.

---

## Table of Contents

- [Section 0: Execution Priority (v3.1)](about:blank#section-0-execution-priority-v31)
- [Section 1: Executive Summary](about:blank#section-1-executive-summary)
- [Section 2: Problem Statement and Pain Points](about:blank#section-2-problem-statement-and-pain-points)
- [Section 3: Goals and Success Metrics](about:blank#section-3-goals-and-success-metrics)
- [Section 4: Personas and Stakeholders](about:blank#section-4-personas-and-stakeholders)
- [Section 5: Canonical Decisions (Locked)](about:blank#section-5-canonical-decisions-locked)
- [Section 6: Epics](about:blank#section-6-epics)
    - [Epic 2 — Auth Abstraction and API Contract Stabilization (P0)](about:blank#epic-2--auth-abstraction-and-api-contract-stabilization-p0)
    - [Epic 3 — OpenSearch Serverless Migration (P1)](about:blank#epic-3--opensearch-serverless-migration-p1)
    - [Epic 4 — S3 PDF Storage (P1)](about:blank#epic-4--s3-pdf-storage-p1)
    - [Epic 5 — BDA Evaluation and Adoption (P1)](about:blank#epic-5--bda-evaluation-and-adoption-p1)
    - [Epic 6 — LLM Strategy: Nova Models (P2)](about:blank#epic-6--llm-strategy-nova-models-p2)
    - [Epic 7 — Deployment Modernization (P2)](about:blank#epic-7--deployment-modernization-p2)
    - [Epic 8 — Knowledge Bases and Agent Core (P3 / Future)](about:blank#epic-8--knowledge-bases-and-agent-core-p3--future)
- [Section 7: System Architecture](about:blank#section-7-system-architecture)
- [Section 8: Data Models](about:blank#section-8-data-models)
- [Section 9: Technical Stack](about:blank#section-9-technical-stack)
- [Section 10: API Contract Reference](about:blank#section-10-api-contract-reference)
- [Section 12: Risk Register](about:blank#section-12-risk-register)
- [Section 13: Roadmap and Timeline](about:blank#section-13-roadmap-and-timeline)
- [Section 14: Development Tooling and DX](about:blank#section-14-development-tooling-and-dx)
- [Section 15: Appendices](about:blank#section-15-appendices)

---

## Section 0: Execution Priority (v3.1)

This section exists at the top of the document intentionally. It is the single most important context for every backend team member before starting any work.

### Delivery Sequence (Backend)

| Priority | Workstream | Why This Order |
| --- | --- | --- |
| **1st** | **Auth abstraction and API contract stabilization** | API consumers (including any UI) require a stable auth flow. Provider-agnostic OIDC and a frozen `/api/*` contract unblock all consumers and prevent rework when migrating from Cognito to Okta. |
| **2nd** | **Search, storage, and extraction** | OpenSearch migration, S3 PDF storage, and BDA evaluation. These establish durable storage and search as the backbone for change detection and retrieval. |
| **3rd** | **LLM strategy and deployment** | Nova/LLM abstraction and deployment modernization (App Runner or EKS for the API). Evaluation work (BDA, Nova models) runs in parallel and feeds into later sprints. |

### What This Means in Practice

- **API contract is frozen** — the existing `/api/*` endpoints and SSE contract are preserved so any client can rely on a stable surface.
- **Backend work proceeds** on auth, OpenSearch, S3, BDA, and LLM in the order above, without blocking on frontend decisions.
- **Evaluation work (BDA, Nova models, hosting)** runs on a separate track and feeds into later sprints.

---

## Section 1: Executive Summary

The **Court Form PDF Monitor** (internally called “URL Monitor” or “Scrappy AI”) is an automated monitoring system designed to detect meaningful changes in court form PDF documents published by judicial councils and superior courts across US jurisdictions.

### What the Backend Does Today

The system operates as a **FastAPI** backend exposing JSON API and SSE. It monitors a registry of URLs for PDF updates, stores version history, detects content changes through a three-tier detection pipeline (HTTP headers, quick hash, full download), provides AI-powered title and form number extraction via AWS Bedrock (Claude), and serves API endpoints for management, review, and triage of detected changes. It integrates with FormsWorkflow (FWF) to maintain organizational parity and supports intelligent relocation detection when court forms move to new URLs.

### What v3.1 Changes (Backend)

Version 3.1 evolves the backend along these dimensions:

1. **Auth and API contract:** Provider-agnostic OIDC with backend-managed sessions (BFF-style). The existing `/api/*` and SSE contract are stabilized so all API consumers have a single, stable surface. Prepares for company-wide migration from Cognito to Okta.
2. **Infrastructure modernization:** AWS Kendra is replaced with OpenSearch Serverless for search. PDF storage moves to S3 as the durable source of truth. Bedrock Document Automation (BDA) is evaluated as a unified replacement for the current Textract + Claude extraction pipeline.
3. **Deployable API service:** The backend is deployable as `url-monitor-api` (FastAPI, JSON-only API + SSE + auth), independent of any specific UI.

### Why This Matters Now

- The **California pilot** and **SteerCo** depend on a reliable, scalable API and auth flow; backend stability is a prerequisite for any client.
- The **AWS Solutions Architecture team** (Matul, Jordan) has recommended OpenSearch over Kendra, BDA for extraction, and Nova Pro for LLM tasks. These recommendations are incorporated into this PRD.
- The **platform vision** — shared infrastructure for Forms Workflow, Court Rules, and future COE projects — requires a robust, contract-stable API as the foundation.

### Current Backend Shape (Repo-Grounded)

- **API:** FastAPI with JSON endpoints and SSE (`/api/monitor/progress/stream`)
- **Auth:** Cognito-based flow currently implemented; target is provider-agnostic OIDC
- **Search:** Kendra-oriented code paths exist; PRD direction is OpenSearch Serverless
- **Core domains:** URL management, change review, triage, audit/metrics, category management
- **PDF processing:** qpdf + pikepdf normalization, pdfplumber + pdfminer.six + Textract OCR extraction
- **AI extraction:** Bedrock (Claude) for title/form number, regex for revision date
- **Deployment:** EKS + Flux GitOps via shared `coe-services` repo

---

## Section 2: Problem Statement and Pain Points

### Original Business Challenge

Court forms published by judicial councils and superior courts across US states are frequently updated, relocated, or deprecated. Legal professionals and organizations need to stay informed about form changes to maintain compliance, track version history for audit purposes, quickly identify when forms are relocated to new URLs, and organize monitored URLs by jurisdiction and category.

### Pain Points (Prioritized)

### P0 — Blocking Demo and Delivery

| # | Pain Point | Impact | Source |
| --- | --- | --- | --- |
| 1 | **Current Jinja2 monolith limits iteration speed.** All JavaScript is inline (400+ lines in base.html alone), no component reuse, no type safety, no modern dev tooling. Every UI change requires full-stack context. | Slows development velocity by 2-3x for UI work. Cannot quickly produce polished demos. | Engineering assessment |
| 2 | **No ability to quickly spin up/down demo environments.** Current EKS + Flux deployment is complex; standing up a new environment requires YAML configuration and cluster access. | SteerCo cannot review features without coordinating with engineering for deployment. | Team meeting transcript |
| 3 | **Long wait times for PDF download and upload.** Observed during Christine’s workflow — periods of minutes waiting for PDF operations. | Users experience frustration and wasted time; unclear if this is network-specific or systemic. | Design session observation |

### P1 — Core Product Gaps

| # | Pain Point | Impact | Source |
| --- | --- | --- | --- |
| 4 | **Manual monitoring of hundreds of court form URLs is time-consuming and error-prone.** Staff must manually check URLs on a regular cadence. | Hours of manual work per week across the monitoring team. | Original PRD v1.0 |
| 5 | **PDF metadata changes create false-positive change alerts.** Timestamps, producer info, and other metadata differ between downloads even when content is identical. | Review time wasted on non-changes; erodes trust in the system. | Original PRD v1.0 |
| 6 | **When forms are relocated, finding the new URL requires manual searching.** No automated way to discover where a form moved to. | Forms go unmonitored until someone manually finds the new location. | Original PRD v1.0 |
| 7 | **No centralized organizational structure for forms.** Forms are not organized by state and category hierarchy in a way that mirrors FormsWorkflow. | Difficult to understand coverage, identify gaps, or sync with FWF. | Original PRD v1.0 |

### P2 — Systemic and Organizational

| # | Pain Point | Impact | Source |
| --- | --- | --- | --- |
| 8 | **Manual handoff between spreadsheets across teams.** The monitoring team, rules attorneys, and Forms Workflow team use separate spreadsheets and shared drives with no unified workflow. | Data gets lost, duplicated, or stale. No single source of truth for form status. | Team meeting transcript |
| 9 | **Court rules team lacks any application layer.** They are “dragging and dropping documents across a web crawler, a shared drive, a SharePoint site” with no purpose-built tool. | Cannot apply AI or automation without a platform layer first. | Team meeting transcript |
| 10 | **Kendra is expensive for our document volume.** AWS Solutions Architects confirmed Kendra is overkill for our use case (a few thousand documents, no web crawling needs). | Unnecessary infrastructure cost; OpenSearch Serverless is cheaper and more flexible. | AWS SA meeting (Matul) |

---

## Section 3: Goals and Success Metrics

### Primary Goals (v3.1) — Backend

| ID | Goal | Success Metric | Target | Current Baseline | How to Measure |
| --- | --- | --- | --- | --- | --- |
| G1 | Stabilize auth and API contract | Provider-agnostic OIDC, frozen `/api/*` and SSE | Contract documented and stable | Cognito coupled | OpenAPI + auth flow docs |
| G2 | Automate PDF change detection | All monitored URLs checked on schedule | 100% coverage | 100% (already complete) | Monitoring cycle completion logs |
| G3 | Eliminate false positives | False positive rate via PDF normalization | < 5% | TBD (measuring) | Change review audit data |
| G4 | Support efficient triage | Batch operations and API for change review | < 30 seconds/change via API | TBD (measuring) | API latency and batch endpoints |
| G5 | Maintain FWF alignment | Sync coverage with FormsWorkflow categories | > 90% match rate | TBD (measuring) | Sync script match report |
| G6 | Migrate search to OpenSearch | Search latency and relevance parity or better | < 500ms p95 latency | Kendra baseline TBD | OpenSearch query metrics |
| G7 | Establish S3 as PDF source of truth | All PDFs stored durably in S3 | 100% of new PDFs | 0% (local only) | S3 object count vs DB version count |
| G8 | Evaluate BDA for extraction | Cost and accuracy comparison complete | Evaluation report published | Not started | Documented evaluation in `/docs/model_evaluations/` |

### Secondary Goals (Backend)

| ID | Goal | Success Metric | Target |
| --- | --- | --- | --- |
| G9 | Provide intelligent relocation suggestions | Top-3 candidates include correct URL | > 80% hit rate |
| G10 | API availability and latency | p99 latency and error rate within SLO | Documented SLOs met |
| G11 | SSE reliability | Progress stream stable for all connected clients | Reconnect and backoff documented |

---

## Section 4: Personas and Stakeholders

Understanding who uses this system and who reviews it is critical for making the right design and priority decisions. These personas are derived from design sessions, user observation, and team discussions.

### Primary Personas

### Monitoring Team Member

- **Role:** Daily operator who manages the URL registry and reviews detected changes.
- **Goals:** Quickly identify real changes vs false positives; batch-process pending changes efficiently; maintain up-to-date URL registry across jurisdictions.
- **Pain points:** Too many false positives waste review time; no way to bulk-process changes efficiently in current workflow; no unified view of monitoring coverage across states.
- **Frequency:** Daily use, 1-2 hours per session.
- **Key workflows:** Dashboard review, URL management, change review, triage, bulk actions.

### Rules Attorney

- **Role:** Legal subject-matter expert who validates form changes and determines downstream impact.
- **Goals:** Understand exactly what changed in a form; determine if the change requires action in downstream systems; maintain compliance with jurisdiction-specific requirements.
- **Pain points:** The level of technical nuance in their work is often underestimated — one attorney described as “basically running scripts” to accomplish manual data tasks. Complex workflows span multiple tools and spreadsheets.
- **Frequency:** Weekly review cycles, deeper dives on flagged changes.
- **Key workflows:** Change review with diff viewer, form detail inspection, audit trail review.

### Forms Workflow Specialist

- **Role:** End-to-end form processor who handles the lifecycle from change detection through vendor submission (NAMI Systems).
- **Goals:** Download changed forms, prepare them for the naming vendor, tag documents with metadata, track the full lifecycle.
- **Pain points:** Long wait times for PDF downloads and uploads observed during workflow sessions; manual handoffs between spreadsheets; the process from detection to vendor submission is not automated.
- **Frequency:** Daily use, extended sessions during monitoring cycles.
- **Key workflows:** Change review, batch download, form detail, category management.

### Secondary Personas

### SteerCo / Leadership Reviewer

- **Role:** Executive stakeholders who review progress and make resourcing decisions.
- **Goals:** See a polished, functional demo of the system; understand progress against milestones; validate the team’s technical direction.
- **Pain points:** Cannot easily access the system without engineering support; need Saturday-report-ready screenshots and walkthroughs.
- **Frequency:** Bi-weekly or monthly demo reviews.
- **Key workflows:** Dashboard overview, metrics, visual inspection of UI quality.

### COE Engineering Team Member

- **Role:** Developer building and maintaining the URL Monitor system and related COE tools.
- **Goals:** Ship features quickly with confidence; maintain code quality; understand the full system architecture.
- **Pain points:** Inline JavaScript in Jinja2 templates makes changes risky; no type safety; no component reuse across pages; complex EKS deployment for simple changes.
- **Frequency:** Daily development.
- **Key workflows:** Local development, testing, deployment, code review.

### AWS Solutions Architect (External Advisory)

- **Role:** AWS technical advisor who reviews architecture decisions and recommends services.
- **Goals:** Help the team use AWS services effectively; recommend cost-optimized approaches.
- **Frequency:** Weekly advisory sessions, in-person meeting at AWS Atlanta office.
- **Key contacts:** Matul (primary SA), Jordan (secondary SA).

---

## Section 5: Canonical Decisions (Locked)

These decisions have been finalized through team discussion, AWS advisory review, and product analysis. They apply identically across all documents and should not be changed without a full team review.

### Decision 1: Execution Priority (Backend)

**Decision:** Auth abstraction and API contract stabilization are the first backend tasks in v3.1 delivery, followed by search, storage, extraction, and deployment.

**Rationale:** All API consumers depend on a stable auth flow and a frozen contract. Delivering provider-agnostic OIDC and a documented, stable `/api/*` and SSE surface unblocks every consumer and prevents rework during the Cognito→Okta migration.

### _FRONTEND_BLOCK_END_

### Decision 2: Auth Strategy

**Decision:** Provider-agnostic OIDC with backend-managed secure HttpOnly session cookies (BFF pattern). Cognito is the temporary provider for the current phase. Okta is the target platform.

**Rationale:**
- **Why BFF over SPA token storage:** Storing JWTs in browser localStorage or sessionStorage exposes them to XSS attacks. The BFF (Backend For Frontend) pattern keeps tokens server-side and issues HttpOnly, Secure, SameSite cookies to the browser. The frontend never sees or stores a raw JWT.
- **Why provider-agnostic OIDC:** The company is migrating from Cognito to Okta. Building an OIDC adapter layer now means the migration is a configuration change (swap the adapter + env vars), not an architecture change.
- **Why Cognito now:** It is already implemented and working. Replacing it before the demo would introduce unnecessary risk.

### Decision 3: API and SSE Contract Preservation (Backend)

**Decision:** The existing `/api/*` endpoints remain the formal contract. The SSE endpoint `/api/monitor/progress/stream` is preserved. All API consumers should use the OpenAPI spec at `/api/openapi.json` for typed clients and documentation.

**Rationale:** The backend API is stable and functional. Freezing the contract allows all consumers to rely on a known, documented surface while the backend team delivers OpenSearch, S3, BDA, and deployment changes without breaking compatibility.

---

## Section 6: Epics

Each epic below is self-contained. It includes enough context, user stories, acceptance criteria, and implementation guidance that the assigned team members can begin work without needing additional architecture decisions.

---

### Epic 1 — UI/UX Framework Rebuild (P0)

**Priority:** P0 — FIRST delivery task in v3.1

**Owner:** Backend Lead, Backend Dev

**Dependencies:** None (can start immediately; builds against existing `/api/*` contract)

**Status:** Planned

### Background and Context

The current frontend is 15 Jinja2 templates with inline JavaScript (400+ lines in `base.html` alone), a single custom CSS file (`static/style.css`), and no component reuse, type safety, or modern dev tooling. Every UI change requires full-stack context because the templates are tightly coupled to the FastAPI backend.

This epic is the first delivery task because:
1. **Demo pressure:** SteerCo needs to see a polished UI for the California pilot review.
2. **Velocity:** The team cannot iterate quickly on UI improvements in the current architecture.
3. **Foundation:** The separated frontend is a prerequisite for the platform vision (shared infrastructure for Forms Workflow + Court Rules).
4. **Parallelism:** Frontend work can proceed immediately because the API contract is frozen.

### User Stories

**US-1.1:** As a monitoring team member, I want to view the dashboard with pending changes, monitoring status, and key metrics so I can quickly understand the current state of the system.

**US-1.2:** As a monitoring team member, I want to manage URLs (add, edit, delete, bulk upload, filter by state/domain) in a responsive data table so I can efficiently maintain the URL registry.

**US-1.3:** As a reviewer, I want to review detected changes with side-by-side diff highlighting, approve/reject actions, and batch operations so I can triage changes quickly.

**US-1.4:** As a user on any page, I want to see real-time monitoring progress via a persistent progress indicator so I know when a monitoring cycle is running and how far along it is.

**US-1.5:** As a user, I want to switch between dark and light themes with my preference persisted across sessions so I can use the application comfortably in any lighting environment.

**US-1.6:** As a SteerCo reviewer, I want the application to look polished and professional with consistent styling, loading states, and error handling so I can confidently present it to stakeholders.

### Scope: Page-by-Page Parity Mapping

Every existing Jinja2 template must be reimplemented as a Next.js route. The table below defines the mapping:

| Current Jinja2 Template | New Next.js Route | Page Component | Key Features to Preserve |
| --- | --- | --- | --- |
| `templates/index.html` | `/` | `DashboardPage` | Monitored URL list with state filter tabs, status badges, change counts |
| `templates/url_management.html` | `/urls` | `URLsPage` | DataTable with state/domain filters, add/edit/delete, bulk upload (CSV/TXT), schedule modal, “Run Cycle Now” button |
| `templates/url_detail.html` | `/urls/[id]` | `URLDetailPage` | URL details, version timeline, change history, diff preview, version comparison |
| `templates/changes.html` | `/changes` | `ChangesPage` | Changes DataTable with type/classification/similarity columns, status filters |
| `templates/change_review.html` | `/changes/[id]` | `ChangeReviewPage` | Diff viewer (overlay + side-by-side), approve/reject actions, relocation suggestions modal, status/type/state filters |
| `templates/triage.html` | `/triage` | `TriagePage` | AI-recommended actions, priority/classification/state filters, batch triage actions |
| `templates/search.html` | `/search` | `SearchPage` | Natural language search input, relevance scores, state/domain filters |
| `templates/metrics.html` | `/metrics` | `MetricsPage` | KPI cards (automation rate, success rate), charts/graphs, performance metrics |
| `templates/audit_metrics.html` | `/audit` | `AuditPage` | Monitoring cycle list, cycle detail drill-down, statistics, trends |
| `templates/category_management.html` | `/categories` | `CategoriesPage` | Hierarchical tree view (left panel), category detail/URLs (right panel), add/edit/delete, drag-and-drop |
| `templates/login.html` | `/login` | `LoginPage` | Email/password form, link to register |
| `templates/register.html` | `/register` | `RegisterPage` | Email, password, confirm password form |
| `templates/confirm.html` | `/confirm` | `ConfirmPage` | Verification code entry |

### Scope: UI Component Inventory

These are the composed components needed, mapped to their shadcn/ui + Radix primitives:

| Component | Source | Usage in URL Monitor |
| --- | --- | --- |
| `DataTable` | TanStack Table + shadcn `Table` | Sortable, filterable tables for URLs, changes, audit logs. Server-side pagination. |
| `Command` | cmdk + shadcn | Global command palette (Cmd+K) for quick navigation and search |
| `Sheet` | Radix + shadcn | Slide-over panels for URL detail editing, filter configuration |
| `Dialog` | Radix + shadcn | Modal dialogs for confirmations, form submissions, bulk upload |
| `Tabs` | Radix + shadcn | Tab navigation for URL detail sections (overview, versions, changes) |
| `Sonner` | sonner toast library | Non-blocking toast notifications for async operations (change detected, cycle complete) |
| `Badge` | shadcn | Status indicators (active, changed, error, archived, new) |
| `Progress` | shadcn | Real-time monitoring progress bars (SSE-driven) |
| `Calendar` + `DateRangePicker` | shadcn | Date range filtering for changes and audit log |
| `Select` / `Combobox` | shadcn | State/category dropdowns with typeahead search |
| `Skeleton` | shadcn | Loading states for async content (every page needs loading skeletons) |
| `Card` | shadcn | Dashboard metric cards, URL summary cards |
| `DiffViewer` | Custom (react-diff-viewer-continued) | Side-by-side text change comparison for change review |
| `TreeView` | Custom (built on Radix Accordion or similar) | Category hierarchy with drag-and-drop |

### Scope: Real-Time Features

- **SSE integration:** Custom `useMonitoringStream()` hook wrapping `EventSource` for `/api/monitor/progress/stream`. Must handle connection lifecycle (open, message, error, reconnect).
- **Polling fallback:** TanStack Query’s `refetchInterval` for environments where SSE is unavailable or disconnects.
- **Optimistic updates:** Immediate UI feedback for triage actions (approve, reject, bulk review) with rollback on server error.
- **Stale-while-revalidate:** Background data refreshing via TanStack Query without blocking loading spinners on subsequent visits.

### Acceptance Criteria

- [ ]  Next.js App Router project scaffolded with TypeScript, Tailwind CSS, shadcn/ui
- [ ]  All 13 pages from the mapping table above are implemented with equivalent functionality
- [ ]  TanStack Table used for all data table views (URLs, changes, audit, triage)
- [ ]  Dark/light theme toggle functional with `next-themes`, preference persisted to `localStorage`
- [ ]  SSE monitoring progress works from the React client via `useMonitoringStream()` hook
- [ ]  All API calls use typed clients generated from or aligned with `/api/openapi.json`
- [ ]  Loading skeletons displayed for every async data fetch
- [ ]  Error boundaries implemented at route level (`error.tsx`) and global level
- [ ]  404 page implemented (`not-found.tsx`)
- [ ]  Global command palette (Cmd+K) functional for page navigation
- [ ]  Toast notifications for async operations (change detected, cycle complete, errors)
- [ ]  Keyboard navigation functional for all interactive elements (WCAG 2.1 AA)
- [ ]  Focus indicators visible for all interactive elements
- [ ]  No critical or major accessibility violations in Axe/Lighthouse audit
- [ ]  Core routes interactive under 2 seconds on standard corporate broadband
- [ ]  Separate Dockerfile for frontend deployment
- [ ]  Application builds and runs independently of the backend (only needs API URL configured)

### Deliverables

1. `url-monitor-ui/` project with complete Next.js application
2. All 13 pages with feature parity
3. `Dockerfile` for frontend container
4. `README.md` with local development setup instructions
5. Component storybook or examples documentation (optional but recommended)

---

### Epic 2 — Auth Abstraction and API Contract Stabilization (P0)

**Priority:** P0 — Second delivery task (frontend needs this to function)

**Owner:** Backend Lead

**Dependencies:** Epic 1 (frontend consumes the auth flow)

**Status:** Planned

### Background and Context

The current auth implementation is tightly coupled to AWS Cognito. The company is migrating to Okta as the standard identity provider. Rather than building for Cognito now and rebuilding for Okta later, we are implementing a provider-agnostic OIDC layer with an adapter pattern. This means the Okta migration becomes a configuration change — swap the adapter and update environment variables — not an architecture rewrite.

The BFF (Backend For Frontend) pattern is chosen over SPA token storage because:
- HttpOnly cookies cannot be accessed by JavaScript, eliminating the most common XSS token theft vector.
- Session lifecycle (creation, refresh, revocation) is managed server-side, giving the backend full control.
- The frontend never sees or stores a raw JWT — it simply sends cookies with every request.

### User Stories

**US-2.1:** As a user, I want to log in with my credentials and have my session managed securely so I do not need to worry about token storage or refresh.

**US-2.2:** As a developer, I want the auth system to use a provider-agnostic OIDC interface so I can switch from Cognito to Okta by changing configuration, not code.

**US-2.3:** As a frontend developer, I want CORS properly configured so the separated frontend can communicate with the backend API without cross-origin errors.

**US-2.4:** As a security reviewer, I want auth tokens stored in HttpOnly, Secure, SameSite cookies so they are not accessible to client-side JavaScript.

### Auth Flow (BFF Pattern)

```
Browser                    Frontend (Next.js)           Backend (FastAPI)          Cognito/Okta
  │                              │                            │                        │
  │  1. Click "Login"            │                            │                        │
  │─────────────────────────────>│                            │                        │
  │                              │  2. POST /api/auth/login   │                        │
  │                              │───────────────────────────>│                        │
  │                              │                            │  3. OIDC token exchange │
  │                              │                            │───────────────────────>│
  │                              │                            │  4. ID + Access tokens  │
  │                              │                            │<───────────────────────│
  │                              │  5. Set-Cookie (HttpOnly)  │                        │
  │                              │<───────────────────────────│                        │
  │  6. Cookie stored by browser │                            │                        │
  │<─────────────────────────────│                            │                        │
  │                              │                            │                        │
  │  7. Subsequent API calls     │                            │                        │
  │  (cookie sent automatically) │                            │                        │
  │─────────────────────────────>│───────────────────────────>│                        │
  │                              │                            │  8. Validate session    │
  │                              │                            │  (from cookie)          │
```

### Configuration

| Variable | Description | Example |
| --- | --- | --- |
| `OIDC_PROVIDER` | Identity provider selector | `cognito` (now), `okta` (target) |
| `OIDC_ISSUER` | OIDC issuer URL for JWT validation | `https://cognito-idp.us-east-1.amazonaws.com/{pool_id}` |
| `OIDC_AUDIENCE` | OIDC audience/client identifier | `{client_id}` |
| `OIDC_CLIENT_SECRET` | Client secret for token exchange | (stored in Secrets Manager) |
| `AUTH_SESSION_COOKIE_NAME` | HttpOnly session cookie name | `url_monitor_session` |
| `AUTH_SESSION_TTL_SECONDS` | Session lifetime | `3600` |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s) for CORS | `https://url-monitor.aderant.com` |

### Acceptance Criteria

- [ ]  Provider-agnostic OIDC interface implemented with adapter pattern
- [ ]  Cognito adapter functional (current provider)
- [ ]  Okta adapter stubbed with interface parity (ready for implementation when Okta is available)
- [ ]  Auth flow uses backend-managed HttpOnly, Secure, SameSite cookies
- [ ]  No JWTs stored in browser localStorage or sessionStorage
- [ ]  Session creation, validation, refresh, and revocation all handled server-side
- [ ]  CORS configured for frontend origin with proper headers
- [ ]  Existing `/api/*` endpoints preserved — no URL changes, no response shape changes
- [ ]  SSE endpoint `/api/monitor/progress/stream` works with cookie-based auth
- [ ]  `/api/openapi.json` (Swagger spec) still accessible and accurate
- [ ]  Environment variables documented in `env.example`
- [ ]  Auth adapter unit tests for both Cognito and Okta interfaces

### Deliverables

1. Provider-agnostic OIDC auth module with adapter pattern
2. Cognito adapter (functional)
3. Okta adapter (interface-ready, stubbed)
4. Updated CORS configuration
5. Updated `env.example` with all auth configuration variables
6. Auth adapter tests

---

### Epic 3 — OpenSearch Serverless Migration (P1)

**Priority:** P1

**Owner:** Backend Dev

**Dependencies:** None (can start in parallel with Epic 1)

**Status:** Planned

### Background and Context

The current search implementation uses AWS Kendra for indexing and searching court form documents. During the AWS Solutions Architecture meeting, Matul (AWS SA) specifically recommended migrating to OpenSearch Serverless for several reasons:

1. **Cost:** Kendra is significantly more expensive for our document volume (a few thousand documents). OpenSearch Serverless removes capacity planning overhead and is priced on actual usage.
2. **Control:** OpenSearch gives full control over index mappings, custom analyzers, and filter chains. Kendra is a managed service where we cannot control which models or processing is used internally.
3. **Extensibility:** OpenSearch supports vector search via neural search plugins. This means we can later add semantic/hybrid search capabilities and use it as the vector store for Bedrock Knowledge Bases (Epic 8) without adding another service.
4. **Features we do not need from Kendra:** Web crawling, managed Q&A, and other enterprise search features that add cost without value for our use case.

### Index Design

| Field | Type | Purpose |
| --- | --- | --- |
| `title` | `text` (analyzed) | Full-text searchable form title |
| `form_number` | `keyword` | Exact-match form number lookup |
| `revision_date` | `date` | Date range filtering |
| `state` | `keyword` | State/jurisdiction facet |
| `domain_category` | `keyword` | Domain category facet |
| `category_id` | `integer` | Category relationship |
| `extracted_text` | `text` (analyzed) | Full-text searchable form content |
| `url` | `keyword` | Source URL |
| `url_id` | `integer` | FK to monitored_urls |
| `version_id` | `integer` | FK to pdf_versions |
| `monitored_url_id` | `integer` | FK to monitored_urls |

**Document ID format:** `url_{url_id}_version_{version_id}` (consistent with existing Kendra document IDs for migration).

**Search strategy:** BM25 keyword search as the baseline. Neural search plugin with an embedding model for optional semantic similarity. Exact approach for the embedding model is TBD (evaluate during implementation), but BM25 + metadata filtering is the minimum viable search experience.

### User Stories

**US-3.1:** As a user, I want to search court forms by title, form number, or content text so I can find specific forms across all jurisdictions.

**US-3.2:** As a user, I want to filter search results by state and category so I can narrow down results to a specific jurisdiction.

**US-3.3:** As a developer, I want the search infrastructure to support future vector search so we can add semantic search without migrating again.

### Code Changes

- **New:** `services/opensearch_client.py` — OpenSearch client wrapper (connection, health check)
- **New:** `services/opensearch_indexer.py` — Document indexing pipeline (index on version creation, update on change)
- **New:** `services/opensearch_search.py` — Search service (query, filter, find-similar)
- **Update:** Database columns `kendra_document_id`, `kendra_indexed_at`, `kendra_index_status` renamed to `opensearch_document_id`, `opensearch_indexed_at`, `opensearch_index_status`
- **New:** One-time migration script to re-index all existing PDF versions into OpenSearch
- **Deprecate:** `services/kendra_*.py` modules (keep for reference, remove from active code paths)

### Configuration

| Variable | Description | Example |
| --- | --- | --- |
| `OPENSEARCH_ENDPOINT` | OpenSearch Serverless endpoint URL | `https://{collection}.us-east-1.aoss.amazonaws.com` |
| `OPENSEARCH_COLLECTION_NAME` | Collection name | `url-monitor-search` |
| `OPENSEARCH_INDEX_NAME` | Index name | `court-forms` |
| `OPENSEARCH_ENABLED` | Feature flag | `true` |

### Acceptance Criteria

- [ ]  OpenSearch Serverless collection and index created with defined field mappings
- [ ]  Indexing pipeline writes PDF metadata and extracted text to OpenSearch on version creation
- [ ]  Search API (`GET /api/search`) returns results from OpenSearch (not Kendra)
- [ ]  Search supports query text, state filter, and domain/category filter
- [ ]  Find-similar-forms behavior (`GET /api/urls/{id}/similar`) preserved or improved
- [ ]  Database columns renamed from `kendra_*` to `opensearch_*` with migration script
- [ ]  One-time re-index script successfully indexes all existing PDF versions
- [ ]  Kendra code paths removed from active execution (can remain in repo for reference)
- [ ]  Search latency under 500ms p95 for typical queries
- [ ]  Search relevance validated against a test set of known queries

### Deliverables

1. OpenSearch Serverless collection and index configuration
2. Three new service modules (`opensearch_client.py`, `opensearch_indexer.py`, `opensearch_search.py`)
3. Database migration script (rename columns)
4. One-time re-index script
5. Updated `env.example` with OpenSearch configuration
6. Search quality validation report

---

### Epic 4 — S3 PDF Storage (P1)

**Priority:** P1

**Owner:** Backend Dev

**Dependencies:** None (can start in parallel)

**Status:** Planned

### Background and Context

Currently, the system does not persistently store downloaded PDFs — it processes them in-memory and stores only the extracted text and metadata in the database. This means:
- We cannot reprocess a PDF without re-crawling the source URL (which may have changed or gone down).
- We have no durable audit trail of the actual documents.
- Future features like Bedrock Knowledge Bases (Epic 8) and BDA (Epic 5) require PDFs in S3.
- Disaster recovery is impossible for historical documents.

S3 is the natural choice for durable PDF storage within the AWS ecosystem. It provides lifecycle rules for cost management (move old documents to cheaper storage tiers), presigned URLs for secure frontend access, and integration with other AWS services.

### S3 Bucket Structure

```
s3://{bucket}/url-monitor/
├── pdfs/
│   ├── raw/                        # Original downloaded PDFs
│   │   └── {url_id}/
│   │       └── {version_id}.pdf
│   └── normalized/                 # Normalized PDFs (post-qpdf/pikepdf)
│       └── {url_id}/
│           └── {version_id}.pdf
├── extracted/                      # Extraction results (JSON)
│   └── {url_id}/
│       └── {version_id}.json       # {title, form_number, revision_date, text, ...}
└── text/                           # Extracted text (for search indexing)
    └── {url_id}/
        └── {version_id}.txt
```

### Lifecycle Rules

| Object Path | Age | Action | Rationale |
| --- | --- | --- | --- |
| `pdfs/raw/*` | 90 days | Move to `STANDARD_IA` | Older raw PDFs accessed infrequently |
| `pdfs/raw/*` | 365 days | Move to `GLACIER` | Archive after 1 year |
| `pdfs/normalized/*` | 180 days | Move to `STANDARD_IA` | Normalized versions accessed less after initial processing |
| `extracted/*` | Never | Keep in `STANDARD` | Small JSON files, frequently accessed for search and display |
| `text/*` | Never | Keep in `STANDARD` | Small text files, used for re-indexing |

### User Stories

**US-4.1:** As a developer, I want all downloaded PDFs stored in S3 so I can reprocess them without re-crawling source URLs.

**US-4.2:** As a reviewer, I want to view and download any historical PDF version so I can audit changes over time.

**US-4.3:** As a compliance officer, I want a durable, auditable record of all form versions we have monitored so we can demonstrate compliance.

### Database Schema Changes

Add columns to the `pdf_versions` table:

```sql
ALTER TABLE pdf_versions ADD COLUMN s3_raw_key VARCHAR(512);
ALTER TABLE pdf_versions ADD COLUMN s3_normalized_key VARCHAR(512);
ALTER TABLE pdf_versions ADD COLUMN s3_extracted_key VARCHAR(512);
ALTER TABLE pdf_versions ADD COLUMN s3_text_key VARCHAR(512);
```

### Code Changes

- **New:** `services/s3_storage.py` with methods:
    - `upload_pdf(url_id, version_id, pdf_bytes, stage)` — Upload to raw or normalized path
    - `download_pdf(s3_key)` — Download PDF bytes from S3
    - `get_presigned_url(s3_key, expiration)` — Generate time-limited download URL for frontend
    - `upload_extraction(url_id, version_id, extraction_result)` — Upload JSON extraction result
    - `upload_text(url_id, version_id, text)` — Upload extracted text
- **Update:** `process_pdf()` to upload to S3 after download and after normalization
- **Update:** PDF download endpoints to serve via presigned URL or proxy from S3
- **Update:** Extraction pipeline to store results in S3 alongside database

### Configuration

| Variable | Description | Example |
| --- | --- | --- |
| `S3_PDF_BUCKET` | Bucket name | `aderant-url-monitor-pdfs` |
| `S3_PDF_PREFIX` | Optional prefix | `url-monitor/` |
| `S3_PDF_STORAGE_CLASS` | Default storage class | `STANDARD` |
| `S3_ENABLED` | Feature flag | `true` |

### Acceptance Criteria

- [ ]  S3 bucket created with defined structure and lifecycle rules
- [ ]  All newly downloaded PDFs uploaded to S3 (raw and normalized)
- [ ]  Extraction results (JSON) and extracted text stored in S3
- [ ]  `pdf_versions` table updated with S3 key columns
- [ ]  Presigned URL generation functional for frontend PDF access
- [ ]  Existing PDF download endpoints work with S3-backed storage
- [ ]  Database migration script adds S3 columns
- [ ]  Feature flag (`S3_ENABLED`) allows gradual rollout
- [ ]  Backfill script to upload existing local PDFs to S3 (optional, P2)

### Deliverables

1. `services/s3_storage.py` module
2. S3 bucket configuration (CloudFormation or Terraform)
3. Database migration script
4. Updated PDF processing pipeline
5. Updated `env.example` with S3 configuration

---

### Epic 5 — BDA Evaluation and Adoption (P1)

**Priority:** P1

**Owner:** Backend Lead, Backend Dev

**Dependencies:** Epic 4 (S3 storage provides PDF access for BDA)

**Status:** Planned (pending evaluation)

### Background and Context

The current extraction pipeline is a multi-step process:
1. **Textract** extracts raw text/layout from the PDF.
2. **Claude (Bedrock)** parses the title and form number from the extracted text via a prompt.
3. **Regex patterns** parse the revision date separately (e.g., “Rev. 01/2026”, “Revised: January 2026”).

This approach works but has limitations: multiple API calls increase latency and cost, and the regex-based revision date extraction misses non-standard or multilingual date formats.

During the AWS SA meeting, Matul recommended evaluating **Bedrock Document Automation (BDA)** as a unified replacement. BDA handles OCR, layout analysis, and structured field extraction in a single API call. It works well for “standard” documents like forms (W-2s, court forms) where field structures can be defined in advance. The key benefit is replacing the two-step Textract + Claude pipeline with a single BDA call.

**Important:** BDA adoption is contingent on a formal evaluation. We do not commit to BDA until the evaluation is complete and results are positive. The legacy Textract + Claude pipeline remains as the fallback.

### Evaluation Framework

Run the following comparison on a dataset of **100+ diverse PDFs** across states, including scanned documents, multilingual forms, and edge cases:

| Metric | Current (Textract + Claude) | BDA | Winner |
| --- | --- | --- | --- |
| Cost per document | $ TBD | $ TBD | TBD |
| Extraction accuracy: title | % TBD | % TBD | TBD |
| Extraction accuracy: form_number | % TBD | % TBD | TBD |
| Extraction accuracy: revision_date | % TBD | % TBD | TBD |
| Latency (avg per document) | ms TBD | ms TBD | TBD |
| Failure rate | % TBD | % TBD | TBD |

**Decision criteria:** BDA wins if it achieves equivalent or better accuracy at equivalent or lower cost, with acceptable latency. If BDA is marginally worse on accuracy but significantly cheaper, the team will discuss the tradeoff.

### BDA Extraction Fields

```json
{
  "title": "string",
  "form_number": "string",
  "revision_date": "string (ISO 8601)",
  "effective_date": "string (ISO 8601) | null",
  "state": "string | null",
  "confidence": {
    "title": 0.0,
    "form_number": 0.0,
    "revision_date": 0.0
  },
  "reasoning": "string"
}
```

### User Stories

**US-5.1:** As a developer, I want to evaluate BDA against our current extraction pipeline so we can make a data-driven decision on adoption.

**US-5.2:** As a monitoring team member, I want extracted title, form number, and revision date to be accurate so I can trust the system’s output without manual verification.

**US-5.3:** As a developer, I want the extraction method to be configurable via feature flag so we can switch between BDA and the legacy pipeline without code changes.

### Code Changes

- **New:** `services/bda_client.py` — BDA API interactions
- **New:** `services/bda_extractor.py` — `extract_document_fields(pdf_bytes) -> ExtractionResult`
- **Update:** `extract_title()` / `process_pdf()` to use BDA when `BDA_ENABLED=true`, falling back to legacy pipeline on failure
- **New:** Evaluation script that runs both pipelines on the test dataset and produces a comparison report

### Configuration

| Variable | Description | Example |
| --- | --- | --- |
| `BDA_ENABLED` | Feature flag for BDA extraction | `false` (until evaluation passes) |
| `BDA_PROJECT_ARN` | BDA project ARN | `arn:aws:bedrock:...` |
| `BDA_BLUEPRINT_ARN` | BDA blueprint ARN | `arn:aws:bedrock:...` |

### Acceptance Criteria

- [ ]  Evaluation dataset of 100+ diverse PDFs assembled
- [ ]  BDA extraction pipeline implemented and functional
- [ ]  Evaluation script runs both pipelines and produces comparison report
- [ ]  Evaluation report published to `/docs/model_evaluations/bda_evaluation.md`
- [ ]  Feature flag (`BDA_ENABLED`) controls which pipeline is used
- [ ]  Legacy Textract + Claude pipeline preserved as fallback
- [ ]  If evaluation is positive: BDA becomes default with legacy fallback
- [ ]  If evaluation is negative: Document findings and revisit in Q3

### Deliverables

1. Evaluation dataset (100+ PDFs)
2. `services/bda_client.py` and `services/bda_extractor.py`
3. Evaluation comparison script
4. Evaluation report (`/docs/model_evaluations/bda_evaluation.md`)
5. Feature-flagged integration in the extraction pipeline

---

### Epic 6 — LLM Strategy: Nova Models (P2)

**Priority:** P2

**Owner:** Backend Dev

**Dependencies:** None

**Status:** Planned

### Background and Context

The system currently defaults to Claude (via Bedrock) for all LLM tasks: title extraction, form number identification, and action recommendations. During the AWS SA meeting, Matul recommended evaluating Amazon Nova models (Nova Pro, Nova Lite) as potentially more cost-effective alternatives for structured extraction tasks.

The guiding principle from the AWS team: **“Always test at least three models before locking in for any new task.”**

This epic establishes a formal model evaluation protocol and abstracts all LLM calls behind a common interface so models can be swapped by configuration.

### Model Comparison

| Model | Provider | Best For | Input Cost (per 1M tokens) | Output Cost (per 1M tokens) | Notes |
| --- | --- | --- | --- | --- | --- |
| Amazon Nova Pro | AWS | Primary extraction, classification | $0.80 | $3.20 | Best balance of cost/capability |
| Amazon Nova Lite | AWS | High-volume, simpler tasks | $0.06 | $0.24 | Lowest cost, fastest |
| Amazon Nova Micro | AWS | Simple classification only | $0.035 | $0.14 | Text only, no vision |
| Claude 3.5 Sonnet | Anthropic | Complex reasoning, fallback | $3.00 | $15.00 | Highest cost, best for edge cases |
| Claude 3 Haiku | Anthropic | Fast, cheap alternative | $0.25 | $1.25 | Good balance |

### Model Evaluation Protocol

1. For each new LLM task (extraction, classification, summarization, etc.):
    - Test at least 3 models from the table above.
    - Evaluate on: accuracy, latency, cost per 1K tokens, and edge case handling.
    - Document results in `/docs/model_evaluations/{task_name}.md`.
2. Re-evaluate quarterly or when new models are released.
3. Primary/fallback model configuration via environment variables.

### User Stories

**US-6.1:** As a developer, I want all LLM calls abstracted behind a common interface so I can switch models by changing configuration, not code.

**US-6.2:** As a product owner, I want a documented model evaluation for each LLM task so we can make cost-informed decisions about which models to use.

### Code Changes

- **New:** `services/llm_client.py` — Abstract interface with `invoke_model(prompt, model_id)` method
- **Update:** All existing Claude/Bedrock calls to use `llm_client.py` instead of direct Bedrock SDK calls
- **Config:** `LLM_MODEL_PRIMARY` (default: `amazon.nova-pro-v1:0`), `LLM_MODEL_FALLBACK` (default: `anthropic.claude-3-sonnet`)

### Acceptance Criteria

- [ ]  `llm_client.py` interface implemented with model selection by config
- [ ]  At least 3 models evaluated for the title/form number extraction task
- [ ]  Evaluation report published to `/docs/model_evaluations/extraction.md`
- [ ]  Primary and fallback model configurable via environment variables
- [ ]  Fallback logic: if primary model fails or returns low confidence, retry with fallback model
- [ ]  All existing LLM calls migrated to use `llm_client.py`
- [ ]  No hardcoded model IDs in application code

### Deliverables

1. `services/llm_client.py` module
2. Model evaluation report for extraction task
3. Updated `env.example` with LLM configuration variables
4. Migration of all existing LLM calls to the new interface

---

### Epic 7 — Deployment Modernization (P2)

**Priority:** P2

**Owner:** Infrastructure Lead

**Dependencies:** Epic 1 (frontend) and Epic 2 (backend auth) — need both services to evaluate deployment

**Status:** Under Evaluation

### Background and Context

The current deployment uses EKS with Flux GitOps via the shared `coe-services` AWS Flux repo. While this works, the team identified several pain points in the meeting transcript:

1. **Setup complexity:** Initial setup of new services requires extensive YAML configuration and cluster access. The team described it as “pretty complex” with the initial setup being “pretty tough.”
2. **No quick demo environments:** SteerCo and stakeholders cannot preview features without coordinating with engineering for deployment. The team needs the ability to “spin something up, spin it down” quickly for internal demos.
3. **Shared infrastructure dependencies:** The EKS cluster is managed by a larger developer team, creating dependencies and permissions issues.

The AWS SA team offered to connect us with App Runner and Amplify specialists for a deeper evaluation.

### Evaluation Matrix

| Criteria | EKS + Flux (Current) | App Runner | Amplify Hosting |
| --- | --- | --- | --- |
| Setup complexity | High (YAML, Flux config, cluster access) | Low (container + config) | Low (git push to deploy) |
| Operational overhead | High (cluster management, scaling config) | Low (fully managed) | Low (fully managed) |
| Container support | Full | Yes | Limited (SSR/Next.js supported) |
| Auto-scaling | Manual configuration | Automatic | Automatic |
| CI/CD integration | Flux GitOps | Built-in from ECR/GitHub | Built-in from GitHub |
| Custom networking | Full VPC control | VPC Connector available | Limited |
| Secrets management | K8s Secrets | Secrets Manager | Secrets Manager |
| Estimated cost at our scale | ~$150+/month | ~$25-50/month | ~$15-30/month |
| Cold starts | None | Possible (mitigated with min instances) | Possible |
| WebSocket/SSE support | Full | Supported | Limited |

### Preliminary Recommendation

| Service | Recommended Platform | Rationale |
| --- | --- | --- |
| Frontend (Next.js) | **Amplify Hosting** | Optimized for Next.js, automatic builds from git, CDN distribution, lowest cost |
| Backend (FastAPI) | **App Runner** or **EKS** | App Runner for simplicity; EKS if VPC/networking requirements are critical |

**Note:** This recommendation is preliminary. The team will prototype both approaches and compare before committing.

### User Stories

**US-7.1:** As a developer, I want to deploy frontend changes by pushing to git so I can iterate quickly without managing infrastructure.

**US-7.2:** As a team lead, I want to spin up a demo environment in minutes so SteerCo can review features without engineering coordination.

**US-7.3:** As an infrastructure lead, I want deployment costs appropriate to our workload size so we are not overpaying for enterprise infrastructure we do not need.

### Acceptance Criteria

- [ ]  Frontend prototype deployed on Amplify Hosting
- [ ]  Backend prototype deployed on App Runner
- [ ]  Cost comparison documented (EKS vs App Runner vs Amplify)
- [ ]  Latency comparison documented
- [ ]  SSE functionality validated on each platform
- [ ]  Developer experience compared (deploy time, debugging, logs)
- [ ]  Decision documented and communicated to team
- [ ]  Follow-up session scheduled with AWS App Runner/Amplify specialists

### Deliverables

1. Prototype deployments (Amplify for frontend, App Runner for backend)
2. Evaluation report comparing all three options
3. Cost analysis
4. Final deployment platform recommendation

---

### Epic 8 — Knowledge Bases and Agent Core (P3 / Future)

**Priority:** P3 — Future scope (not in v3.1 delivery commitment)

**Owner:** TBD

**Dependencies:** Epic 3 (OpenSearch), Epic 4 (S3 storage)

**Status:** Future (architecture proposal only in v3.1)

### Background and Context

This epic captures the longer-term platform vision discussed in the team meeting. The team envisions a shared infrastructure that serves both Forms Workflow and Court Rules (and potentially other COE projects) through a common platform with modular workflows.

Key insights from the meeting transcript:
- “Instead of building apps, we build out that platform” — the goal is a shared platform with modular components, not separate applications.
- “The infrastructure will be the same, the application will be the same, but it will look a little bit different based on the workflows and the requirements.”
- The Court Rules team currently has no application layer — they are working with SharePoint, shared drives, and spreadsheets.
- The vision for 2027 is to offer court rules monitoring as a subscription service to other companies.

### Bedrock Knowledge Bases

**What:** Managed RAG (Retrieval-Augmented Generation) for chat/Q&A over monitored documents.

**When:** If/when we add conversational search features (e.g., “What changed in California family law forms this quarter?”).

**How it connects:**

```
S3 (pdfs/normalized/)
    ↓ [auto-sync]
Bedrock Knowledge Base
    ↓ [chunking + embedding]
OpenSearch Serverless (vector index)
    ↓ [RAG query]
Bedrock LLM (Nova Pro / Claude)
    ↓
Natural language answer
```

**Prerequisites:**
- S3 storage of PDFs (Epic 4) must be in place.
- OpenSearch Serverless (Epic 3) can serve as the vector store.

**Potential use cases:**
- “What are the new filing requirements in FL-100?”
- “Compare the changes between v2 and v3 of form JC-001.”
- “Which California forms were updated in January 2026?”

### Agent Core and Strands Framework

**What:** Multi-step agentic workflows for complex automation tasks.

**When:** When we need workflows that involve:
- Multi-step reasoning with tool use (API calls, database queries, file operations)
- Memory and context management across sessions
- Complex orchestration across multiple services
- Built-in observability for debugging and evaluation

**Framework comparison:**

| Feature | Bedrock Agent Core | Strands | LangGraph |
| --- | --- | --- | --- |
| AWS native | Yes | Yes | No |
| Bedrock integration | Deep | Native | Manual |
| Tool orchestration | Built-in | Built-in | Built-in |
| Memory management | Managed | Managed | Manual |
| Observability | Built-in | Built-in | Manual |
| MCP support | Yes | Yes | Via plugin |

**Target use cases (future):**
- **Forms Workflow automation:** End-to-end processing from change detection through FWF update.
- **Court Rules monitoring:** Automated rule change detection and impact analysis.
- **Intelligent triage:** AI-powered recommendations for change classification with learning from reviewer decisions.
- **Proactive alerts:** Agent-driven notifications based on change patterns.

### Deliverables (v3.1 only)

1. Architecture proposal document describing how Knowledge Bases and Agent Core would integrate with the URL Monitor platform.
2. No implementation in v3.1. Implementation begins in v3.2 (Q4 2026) at the earliest.

---

## Section 7: System Architecture

### Current State (v3.0 — Monolith)

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Court Form PDF Monitor (Monolith)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────┐   ┌───────────────┐   ┌──────────────────────────┐   │
│  │   URL     │   │   Fetcher     │   │    PDF Processing        │   │
│  │ Registry  │──▶│ (AWS Lambda)  │──▶│  qpdf → pikepdf          │   │
│  │ (Postgres)│   │               │   │  pdfplumber → Textract   │   │
│  └───────────┘   └───────────────┘   └──────────────────────────┘   │
│                                               │                      │
│                                               ▼                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Change Detection                            │  │
│  │   HTTP Headers → Quick Hash → Full Download → Text Diff       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                               │                      │
│                         ┌─────────────────────┴───────────────┐      │
│                         ▼                                     ▼      │
│                  ┌──────────────┐                   ┌──────────────┐ │
│                  │   Storage    │                   │  PostgreSQL  │ │
│                  │ (Local FS)   │                   │  Database    │ │
│                  └──────────────┘                   └──────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Monolith: Jinja2 templates + JSON API + SSE + Auth   │  │
│  │  (single container, single K8s deployment via EKS + Flux)     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────┐   ┌────────────────────────┐                 │
│  │  AWS Kendra       │   │  AWS Bedrock (Claude)   │                │
│  │  (search index)   │   │  (title extraction)     │                │
│  └───────────────────┘   └────────────────────────┘                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Target State (v3.1 — Separated Frontend/Backend)

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Court Form PDF Monitor (v3.1)                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐ │
│  │  url-monitor-ui (Frontend)   │  │  url-monitor-api (Backend)   │ │
│  │                              │  │                              │ │
│  │  Next.js App Router          │  │  FastAPI, JSON-only API      │ │
│  │  React + TypeScript          │  │  /api/* endpoints            │ │
│  │  Tailwind CSS + shadcn/ui    │──▶│  SSE: /api/monitor/         │ │
│  │  TanStack Table + Query      │  │       progress/stream        │ │
│  │  next-themes (dark/light)    │  │  Auth: OIDC BFF (HttpOnly    │ │
│  │                              │  │        session cookies)      │ │
│  │  Deployed: Amplify or Docker │  │  Deployed: App Runner or EKS │ │
│  └──────────────────────────────┘  └──────────────┬───────────────┘ │
│                                                    │                 │
│          ┌─────────────────────────────────────────┼───────────┐     │
│          │                                         │           │     │
│          ▼                                         ▼           ▼     │
│  ┌──────────────┐   ┌─────────────────────┐  ┌────────────────────┐│
│  │  PostgreSQL   │   │  S3 (PDF Storage)   │  │ OpenSearch         ││
│  │  Database     │   │  raw/normalized/    │  │ Serverless         ││
│  │              │   │  extracted/text     │  │ (search index)     ││
│  └──────────────┘   └─────────────────────┘  └────────────────────┘│
│                                                                      │
│  ┌───────────────────────────┐  ┌────────────────────────────────┐  │
│  │  AWS Bedrock              │  │  AWS Lambda                    │  │
│  │  - BDA (evaluation)       │  │  (PDF crawler/fetcher)         │  │
│  │  - Nova Pro / Claude      │  │                                │  │
│  │  - LLM abstraction layer  │  │                                │  │
│  └───────────────────────────┘  └────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Auth: Cognito (now) → Okta (target)                          │  │
│  │  Provider-agnostic OIDC with backend-managed sessions         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Monitoring Cycle

```
1. Scheduler triggers monitoring cycle (APScheduler or manual "Run Now")
2. For each monitored URL in the registry:
   a. Tier 1: Check HTTP headers (ETag, Last-Modified) for quick change signal
   b. Tier 2: Quick hash comparison (if headers suggest change)
   c. Tier 3: Full PDF download via Lambda
3. Downloaded PDF → normalize (qpdf + pikepdf) → upload to S3 (raw + normalized)
4. Extract text (pdfplumber → pdfminer → Textract OCR fallback)
5. Extract metadata (BDA or Claude: title, form_number, revision_date)
6. Compare with previous version (text hash, per-page hash, text diff)
7. If changed: create ChangeLog entry, index in OpenSearch, notify via SSE
8. Store all results in PostgreSQL; PDFs in S3
9. SSE stream updates progress to all connected frontend clients
```

---

## Section 8: Data Models

### Core Tables

| Table | Description | Key Columns |
| --- | --- | --- |
| `states` | US states/jurisdictions (top-level org) | `id`, `name`, `abbreviation`, `is_active`, `created_at`, `updated_at` |
| `categories` | Hierarchical categories within states | `id`, `name`, `description`, `parent_category_id` (self-ref), `state_id`, `full_path` |
| `monitored_urls` | Registry of URLs to monitor | `id`, `url`, `title`, `form_number`, `revision_date`, `state_id`, `category_id`, `is_enabled`, `last_checked`, `status` |
| `pdf_versions` | Stored PDF versions with hashes | `id`, `url_id`, `version_number`, `pdf_hash`, `text_hash`, `normalized_hash`, `file_path`, `text_content`, `s3_raw_key` (new), `s3_normalized_key` (new), `s3_extracted_key` (new), `s3_text_key` (new), `opensearch_document_id` (renamed from kendra), `opensearch_indexed_at` (renamed), `opensearch_index_status` (renamed), `created_at` |
| `change_log` | Record of detected changes | `id`, `url_id`, `version_id`, `change_type`, `classification`, `confidence`, `reasoning`, `status`, `reviewed_by`, `reviewed_at`, `created_at` |
| `monitoring_cycles` | Audit trail of monitoring executions | `id`, `started_at`, `completed_at`, `total_urls`, `changes_detected`, `errors`, `status` |
| `cycle_url_results` | Per-URL results within a monitoring cycle | `id`, `cycle_id`, `url_id`, `status`, `change_detected`, `error_message`, `duration_ms` |
| `schedule_config` | User-configurable schedule settings | `id`, `cron_expression`, `is_enabled`, `last_run`, `next_run` |

### Key Relationships

```
State (1) ──────────────────── (N) Category
                                    │
Category (1) ───────────────── (N) Category (self-referential for nesting)
                                    │
Category (1) ───────────────── (N) MonitoredURL
                                    │
MonitoredURL (1) ──────────── (N) PDFVersion
                                    │
PDFVersion (1) ────────────── (N) ChangeLog

MonitoringCycle (1) ────────── (N) CycleURLResult
CycleURLResult (N) ────────── (1) MonitoredURL
```

### v3.1 Schema Changes

1. **S3 storage columns** added to `pdf_versions` (see Epic 4):
    - `s3_raw_key`, `s3_normalized_key`, `s3_extracted_key`, `s3_text_key`
2. **OpenSearch columns** renamed from Kendra (see Epic 3):
    - `kendra_document_id` → `opensearch_document_id`
    - `kendra_indexed_at` → `opensearch_indexed_at`
    - `kendra_index_status` → `opensearch_index_status`

---

## Section 9: Technical Stack

### Current State vs Target State

| Layer | Current (v3.0) | Target (v3.1) | Epic |
| --- | --- | --- | --- |
| **Frontend framework** | Jinja2 server-rendered templates | Next.js 15+ App Router | Epic 1 |
| **Frontend language** | Inline JavaScript (no types) | TypeScript 5+ | Epic 1 |
| **Styling** | Custom CSS (`static/style.css`) | Tailwind CSS 4+ | Epic 1 |
| **Component library** | None (raw HTML) | shadcn/ui (Radix primitives) | Epic 1 |
| **Data tables** | Custom HTML tables | TanStack Table v8 | Epic 1 |
| **Server state** | Inline fetch calls | TanStack Query v5 | Epic 1 |
| **Global state** | None | Zustand | Epic 1 |
| **Forms** | Raw HTML forms | React Hook Form + Zod | Epic 1 |
| **Theme** | Custom CSS variables + JS toggle | next-themes | Epic 1 |
| **Icons** | None (text labels) | Lucide React | Epic 1 |
| **Auth** | Cognito (tightly coupled) | Provider-agnostic OIDC / BFF | Epic 2 |
| **Auth tokens** | Mixed (JWT in responses) | HttpOnly session cookies | Epic 2 |
| **Search** | AWS Kendra | OpenSearch Serverless | Epic 3 |
| **PDF storage** | Local filesystem / in-memory | S3 | Epic 4 |
| **Extraction** | Textract + Claude + regex | BDA (if evaluation positive) + fallback | Epic 5 |
| **LLM** | Claude (hardcoded) | Abstracted interface (Nova Pro primary) | Epic 6 |
| **Deployment** | EKS + Flux (single container) | Amplify + App Runner or EKS (two containers) | Epic 7 |

### Frontend Technology Stack Detail (v3.1)

| Layer | Technology | Version | Rationale |
| --- | --- | --- | --- |
| Framework | Next.js (App Router) | 15+ | Server components, layouts, API routes, SSR/SSG, optimized builds |
| Language | TypeScript | 5+ | Type safety, refactoring, IDE support |
| Styling | Tailwind CSS | 4+ | JIT mode, design tokens, rapid iteration |
| Component library | shadcn/ui | Latest | Accessible, customizable, project-owned components |
| Primitives | Radix UI | Latest | Unstyled, accessible primitives (dialogs, popovers, dropdowns, menus) |
| Server state | TanStack Query (React Query) | v5 | Caching, background refetch, optimistic updates |
| Global state | Zustand | Latest | Lightweight global state (theme, user session, UI preferences) |
| Forms | React Hook Form + Zod | Latest | Performant forms with schema-based validation |
| Theme | next-themes | Latest | Dark/light mode with system preference detection |
| Class utils | clsx + class-variance-authority | Latest | Conditional class composition, variant management |
| Icons | Lucide React | Latest | Consistent, tree-shakeable icon set |
| Charts | Recharts (or Tremor) | Latest | Metrics visualizations |
| Tables | TanStack Table | v8 | Headless, performant data tables |
| Date handling | date-fns | Latest | Lightweight date formatting |
| HTTP client | ky or native fetch | Latest | Lightweight API calls (wrapped in TanStack Query) |
| Diff viewer | react-diff-viewer-continued | Latest | Side-by-side text comparison |
| Testing (E2E) | Playwright | Latest | Cross-browser E2E testing |
| Testing (Unit) | Vitest + React Testing Library | Latest | Fast unit/integration tests |
| Linting | ESLint + Prettier + Tailwind IntelliSense | Latest | Consistent code quality |
| Build | Turbopack (via Next.js) | Latest | Fast development builds |

### Backend Technology Stack (unchanged except additions)

| Layer | Technology | Notes |
| --- | --- | --- |
| Runtime | Python 3.x | No change |
| Framework | FastAPI + Uvicorn | JSON-only API (Jinja2 templates removed) |
| Database | PostgreSQL (prod), SQLite (dev) | No change |
| ORM | SQLAlchemy | No change |
| PDF processing | qpdf, pikepdf, pdfplumber, pdfminer.six | No change |
| OCR | AWS Textract | No change (also used as BDA fallback) |
| AI/ML | AWS Bedrock (BDA, Nova, Claude) | Epic 5, 6 |
| Search | OpenSearch Serverless | Epic 3 (replaces Kendra) |
| Object storage | AWS S3 | Epic 4 (new) |
| LLM abstraction | `llm_client.py` | Epic 6 (new) |
| Web scraping | AWS Lambda | No change |
| Scheduling | APScheduler | No change |
| Auth | Provider-agnostic OIDC (BFF) | Epic 2 (replaces tight Cognito coupling) |

---

## Section 10: API Contract Reference

These are the existing API endpoints that serve as the formal contract between frontend and backend. All endpoints are preserved in v3.1. The frontend must be built against these exact paths.

Full OpenAPI spec is available at `/api/docs` (Swagger UI) and `/api/openapi.json`.

### States and Categories

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/states` | List all states/jurisdictions |
| `GET` | `/api/states/{state_id}` | Get state details |
| `POST` | `/api/states` | Create a new state |
| `PUT` | `/api/states/{state_id}` | Update state |
| `GET` | `/api/categories` | List all categories |
| `GET` | `/api/categories/tree` | Get full category hierarchy tree |
| `GET` | `/api/categories/{category_id}` | Get category details |
| `GET` | `/api/categories/{category_id}/children` | Get child categories |
| `GET` | `/api/categories/{category_id}/urls` | Get URLs in a category |
| `POST` | `/api/categories` | Create a new category |
| `PUT` | `/api/categories/{category_id}` | Update category |
| `DELETE` | `/api/categories/{category_id}` | Delete category |

### URL Management

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/urls` | List monitored URLs with pagination and filters |
| `GET` | `/api/url-filters` | Get available filter options (states, statuses, etc.) |
| `POST` | `/api/urls` | Create a new monitored URL |
| `GET` | `/api/urls/{url_id}` | Get URL details |
| `PUT` | `/api/urls/{url_id}` | Update URL |
| `DELETE` | `/api/urls/{url_id}` | Delete URL |
| `GET` | `/api/urls/{url_id}/versions` | List PDF versions for a URL |
| `GET` | `/api/urls/{url_id}/versions/{version_id}/pdf` | Download PDF file |
| `GET` | `/api/urls/{url_id}/versions/{version_id}/text` | Get extracted text |
| `GET` | `/api/urls/{url_id}/versions/{version_id}/preview` | Preview PDF |
| `GET` | `/api/urls/{url_id}/versions/{version_id}/diff-preview` | Get visual diff preview |
| `GET` | `/api/urls/{url_id}/versions/{version_id}/diff-info` | Get diff metadata |
| `POST` | `/api/urls/{url_id}/versions/{version_id}/extract-title` | Re-run title extraction |
| `GET` | `/api/urls/{url_id}/similar` | Find similar/relocated URLs |
| `POST` | `/api/urls/bulk-delete` | Bulk delete URLs |
| `POST` | `/api/urls/bulk-upload` | Bulk upload URLs from CSV/TXT |
| `GET` | `/api/urls/upload-template` | Download bulk upload template |
| `GET` | `/api/urls/upload-guide` | Get upload format guide |

### Changes and Triage

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/changes` | List detected changes with filters |
| `GET` | `/api/changes-full` | List changes with full detail (including text diffs) |
| `GET` | `/api/changes/{change_id}/download` | Download changed PDF |
| `POST` | `/api/changes/{change_id}/approve` | Approve a change |
| `POST` | `/api/changes/{change_id}/unapprove` | Revert change approval |
| `POST` | `/api/changes/{change_id}/intervention` | Record manual intervention |
| `POST` | `/api/triage/review/{change_id}` | Review a single change |
| `POST` | `/api/triage/bulk-review` | Bulk review multiple changes |
| `POST` | `/api/triage/override/{change_id}` | Override AI classification |
| `POST` | `/api/triage/auto-approve-eligible` | Auto-approve eligible changes |
| `POST` | `/api/triage/approve-all-pending` | Approve all pending changes |
| `POST` | `/api/triage/dismiss-false-positives` | Dismiss false positives |

### Monitoring

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/monitor/run` | Start a monitoring cycle |
| `POST` | `/api/monitor/run-now` | Run monitoring cycle immediately |
| `GET` | `/api/monitor/progress` | Get current monitoring progress (polling) |
| `GET` | `/api/monitor/progress/stream` | **SSE stream** for real-time monitoring progress |
| `GET` | `/api/status` | Get system status |

### Metrics and Audit

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/metrics` | Get system metrics |
| `GET` | `/api/metrics/accuracy` | Get extraction accuracy metrics |
| `GET` | `/api/metrics/jurisdiction` | Get per-jurisdiction metrics |
| `GET` | `/api/aws-calls` | Get AWS API call counts |
| `GET` | `/api/audit/cycles` | List monitoring cycles |
| `GET` | `/api/audit/cycles/{cycle_id}` | Get cycle details |
| `GET` | `/api/audit/cycles/{cycle_id}/results` | Get per-URL results for a cycle |
| `GET` | `/api/audit/stats` | Get audit statistics |
| `GET` | `/api/audit/trends` | Get audit trends over time |

### Search

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/search` | Search indexed documents (query, state filter, category filter) |

### Kendra (Legacy — To Be Removed in v3.1)

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/kendra/index/{version_id}` | Index a version in Kendra (deprecated) |
| `GET` | `/api/kendra/status` | Get Kendra index status (deprecated) |

### Scheduling

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/schedule` | Get current schedule configuration |
| `PUT` | `/api/schedule` | Update schedule configuration |

---

## Section 11: Frontend Implementation Guide

This section provides detailed implementation guidance for the UI rebuild (Epic 1). It is intended to be read alongside the epic’s acceptance criteria.

### Project Structure

```
url-monitor-ui/
├── app/                              # Next.js App Router
│   ├── (auth)/                       # Auth group layout (minimal chrome)
│   │   ├── layout.tsx
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── confirm/page.tsx
│   ├── (dashboard)/                  # Main app group layout (sidebar, nav)
│   │   ├── layout.tsx
│   │   ├── page.tsx                  # Dashboard home (/)
│   │   ├── urls/
│   │   │   ├── page.tsx              # URL Management list
│   │   │   └── [id]/
│   │   │       ├── page.tsx          # URL Detail view
│   │   │       └── loading.tsx       # Loading skeleton
│   │   ├── changes/
│   │   │   ├── page.tsx              # Changes list
│   │   │   └── [id]/page.tsx         # Change Review detail
│   │   ├── triage/page.tsx           # Batch triage operations
│   │   ├── search/page.tsx           # OpenSearch-powered search
│   │   ├── metrics/page.tsx          # System metrics and stats
│   │   ├── audit/page.tsx            # Audit log viewer
│   │   └── categories/page.tsx       # Category management
│   ├── api/                          # Next.js Route Handlers (optional BFF)
│   │   └── auth/[...nextauth]/route.ts
│   ├── layout.tsx                    # Root layout (providers, fonts, metadata)
│   ├── loading.tsx                   # Global loading state
│   ├── error.tsx                     # Global error boundary
│   └── not-found.tsx                 # 404 page
├── components/
│   ├── ui/                           # shadcn/ui primitives (auto-generated)
│   │   ├── button.tsx, card.tsx, dialog.tsx, dropdown-menu.tsx
│   │   ├── input.tsx, select.tsx, sheet.tsx, skeleton.tsx
│   │   ├── table.tsx, tabs.tsx, toast.tsx (sonner), badge.tsx
│   │   ├── command.tsx (cmdk), calendar.tsx, progress.tsx
│   │   └── ...
│   ├── forms/                        # Composed form components
│   │   ├── url-form.tsx
│   │   ├── filter-form.tsx
│   │   ├── category-form.tsx
│   │   └── search-form.tsx
│   ├── tables/                       # Data table implementations
│   │   ├── urls-table/
│   │   │   ├── columns.tsx           # Column definitions
│   │   │   ├── data-table.tsx        # Table component
│   │   │   └── toolbar.tsx           # Filter toolbar
│   │   ├── changes-table/
│   │   └── audit-table/
│   ├── charts/                       # Metrics visualizations
│   │   ├── monitoring-chart.tsx
│   │   ├── changes-over-time.tsx
│   │   └── status-distribution.tsx
│   └── layout/                       # Layout components
│       ├── sidebar.tsx
│       ├── navbar.tsx
│       ├── breadcrumbs.tsx
│       ├── command-menu.tsx          # Global Cmd+K command palette
│       └── theme-toggle.tsx
├── features/                         # Feature-based modules
│   ├── auth/
│   │   ├── hooks/use-auth.ts
│   │   ├── components/login-form.tsx
│   │   └── api/auth-api.ts
│   ├── urls/
│   │   ├── hooks/use-urls.ts
│   │   ├── hooks/use-url-detail.ts
│   │   ├── api/urls-api.ts
│   │   └── types.ts
│   ├── changes/
│   │   ├── hooks/use-changes.ts
│   │   ├── api/changes-api.ts
│   │   └── components/diff-viewer.tsx
│   ├── search/
│   │   ├── hooks/use-search.ts
│   │   └── api/search-api.ts
│   └── monitoring/
│       ├── hooks/use-monitoring-stream.ts  # SSE hook
│       └── components/progress-card.tsx
├── hooks/                            # Shared custom hooks
│   ├── use-debounce.ts
│   ├── use-local-storage.ts
│   └── use-media-query.ts
├── lib/                              # Utilities
│   ├── api-client.ts                 # Configured fetch/ky instance
│   ├── utils.ts                      # cn() helper, formatters
│   ├── constants.ts
│   └── validators.ts                 # Zod schemas
├── providers/                        # React context providers
│   ├── query-provider.tsx            # TanStack Query
│   ├── theme-provider.tsx            # next-themes
│   └── auth-provider.tsx             # Auth context
├── styles/
│   └── globals.css                   # Tailwind directives, CSS variables
├── types/                            # Shared TypeScript types
│   ├── api.ts, url.ts, change.ts, user.ts
├── public/                           # Static assets
│   ├── favicon.ico
│   └── images/
├── tailwind.config.ts
├── components.json                   # shadcn/ui configuration
├── next.config.ts
├── tsconfig.json
├── package.json
└── Dockerfile
```

### Design System

### Color Tokens (CSS Variables)

These tokens power both light and dark themes via Tailwind and `next-themes`:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 210 40% 98%;
  --primary-foreground: 222.2 47.4% 11.2%;
  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 212.7 26.8% 83.9%;
}
```

### Typography

- **Font:** Inter via `next/font` (system fallback: SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI)
- **Scale:** Use Tailwind defaults (`text-sm`, `text-base`, `text-lg`, etc.)

### Accessibility Requirements (WCAG 2.1 AA)

- All Radix primitives provide WCAG 2.1 AA compliance out of the box. Do not override accessibility attributes.
- Full keyboard navigation with visible focus indicators on all interactive elements.
- Screen reader support with proper ARIA attributes and live regions (especially for SSE progress updates).
- Reduced motion support via `prefers-reduced-motion` media query.
- Color contrast ratios meeting AA standards (4.5:1 for normal text, 3:1 for large text) in both light and dark themes.
- Skip links for main content navigation.

### Performance Budgets

| Metric | Target | How to Measure |
| --- | --- | --- |
| Time to Interactive (TTI) | < 2 seconds | Lighthouse on corporate broadband profile |
| First Contentful Paint (FCP) | < 1 second | Lighthouse |
| Largest Contentful Paint (LCP) | < 2.5 seconds | Lighthouse |
| Cumulative Layout Shift (CLS) | < 0.1 | Lighthouse |
| JavaScript bundle (initial route) | < 200 KB gzipped | `@next/bundle-analyzer` |

### UI Parity Checklist: URL Management

The URL Management page is the most feature-dense view. These specific behaviors must be preserved:

- [ ]  State and domain filter dropdowns (server-side filtering)
- [ ]  Full-text search across URL, title, form number
- [ ]  DataTable with columns: URL, title, form number, state, status, last checked, changes
- [ ]  Row click navigates to URL detail
- [ ]  Add URL modal/sheet with form validation
- [ ]  Edit URL inline or via modal
- [ ]  Delete URL with confirmation dialog
- [ ]  Bulk upload via CSV/TXT file with progress indicator
- [ ]  Schedule configuration modal (cron expression, enable/disable)
- [ ]  “Run Cycle Now” button with confirmation
- [ ]  Server-side pagination (page size selector, page navigation)
- [ ]  Schedule status indicator (next run, last run)

### UI Parity Checklist: Change Review

- [ ]  Status, type, and state filter dropdowns
- [ ]  DataTable with columns: form title, form number, change type, classification, confidence, state, date
- [ ]  Row click opens change detail
- [ ]  Diff preview (overlay mode and side-by-side mode)
- [ ]  Relocation suggestions modal (top 3 candidates with similarity scores)
- [ ]  Approve button with audit tracking
- [ ]  Intervention recording
- [ ]  Bulk actions (approve all, dismiss false positives)

### UI Parity Checklist: Global Progress (SSE)

- [ ]  Fixed-position progress indicator visible on all pages (not just dashboard)
- [ ]  Real-time updates via SSE (`/api/monitor/progress/stream`)
- [ ]  Shows: current URL being checked, overall progress percentage, estimated time remaining
- [ ]  Graceful handling of SSE disconnection (reconnect or fall back to polling)
- [ ]  Toast notification when monitoring cycle completes or detects changes

---

## Section 12: Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| R1 | **UI rebuild scope creep.** Adding new features during parity rebuild extends timeline. | High | High | Strict parity-first policy: no new features until all 13 pages have equivalent functionality. New feature requests go to a backlog, not the current sprint. | Backend Lead |
| R2 | **Auth migration complexity.** OIDC abstraction introduces new failure modes during the Cognito→Okta transition. | Medium | High | Adapter pattern with comprehensive tests for both providers. Feature flag to fall back to direct Cognito if adapter fails. Okta adapter is stubbed now, fully implemented later. | Backend Lead |
| R3 | **BDA evaluation timeline.** Assembling 100+ diverse PDFs and running comparisons may take longer than expected. | Medium | Medium | Start PDF collection immediately (parallel with other work). Accept a smaller initial dataset (50 PDFs) for preliminary evaluation, expand later. Keep legacy pipeline as production default until evaluation is conclusive. | Backend Lead |
| R4 | **Team bandwidth and tight deadlines.** California pilot and SteerCo demos create pressure to cut corners. | High | High | Divide-and-conquer epic ownership: frontend and backend work in parallel. Clear acceptance criteria define “done” for each epic. Sprint-level roadmap (Section 13) provides visibility into what fits in each sprint. | Tech Lead |
| R5 | **Court rules shared platform vision vs. isolated delivery.** Pressure to build shared infrastructure before Forms Workflow is stable. | Medium | Medium | Platform vision is documented in Epic 8 as future scope. v3.1 focuses exclusively on Forms Workflow. Court rules discussions continue separately but do not block v3.1 delivery. | Tech Lead |
| R6 | **OpenSearch migration data integrity.** Re-indexing could miss documents or produce different search results. | Low | High | Parallel run: keep Kendra active during migration. Validation script compares search results from both systems on a test query set. Only switch over when validation passes. | Backend Dev |
| R7 | **Demo environment readiness.** SteerCo expects polished demos on tight timelines. | High | Medium | Deploy to staging early and often. Epic 1 deliverables are prioritized for staging deployment. Use current EKS deployment for initial staging; Amplify/App Runner evaluation (Epic 7) follows. | Infrastructure Lead |
| R8 | **SSE compatibility across deployment platforms.** Some managed hosting options (Amplify) have limited SSE support. | Medium | Medium | Validate SSE on each platform during Epic 7 evaluation. Implement polling fallback in the frontend (TanStack Query `refetchInterval`) as a safety net. | Backend Lead |

---

## Section 13: Roadmap and Timeline

### Q1 2026 — Completed (Current Sprint)

These features are already implemented and working in the current monolith:

- [x]  Automated scheduling (APScheduler, configurable cron)
- [x]  Three-tier change detection (HTTP headers → quick hash → full download)
- [x]  PDF normalization (qpdf + pikepdf)
- [x]  Text extraction (pdfplumber → pdfminer → Textract OCR)
- [x]  Batch download (ZIP export with CSV manifest)
- [x]  State and category database models
- [x]  Global progress bar (SSE)
- [x]  FormsWorkflow sync script (`sync_fwf_tree.py`)
- [x]  Enhanced similarity scoring (TF-IDF + URL/filename matching)
- [x]  Non-blocking monitoring (background execution)
- [x]  URL management (CRUD, bulk upload, pagination)
- [x]  Change review (diff preview, approve/reject)
- [x]  Audit and metrics (cycle tracking, statistics)
- [x]  Kendra search integration (deployed, functional)
- [ ]  Category management UI (in progress)

### Q2 2026 — v3.1 Delivery (Sprint Plan)

### Sprint 1 (Weeks 1-2): Foundation

| Task | Epic | Owner | Dependencies |
| --- | --- | --- | --- |
| Scaffold `url-monitor-ui` with Next.js, TypeScript, Tailwind, shadcn/ui | Epic 1 | Backend Lead | None |
| Implement root layout, auth layout, dashboard layout | Epic 1 | Backend Lead | None |
| Implement Dashboard page (metric cards, URL list, status indicators) | Epic 1 | Backend Dev | Scaffold complete |
| Implement Login, Register, Confirm pages | Epic 1 | Backend Dev | Auth layout complete |
| Create OpenSearch Serverless collection and index | Epic 3 | Backend Dev | None |
| Implement `opensearch_client.py`, `opensearch_indexer.py` | Epic 3 | Backend Dev | Collection created |
| Begin PDF collection for BDA evaluation dataset | Epic 5 | Backend Lead | None |

### Sprint 2 (Weeks 3-4): Core Pages + Infrastructure

| Task | Epic | Owner | Dependencies |
| --- | --- | --- | --- |
| Implement URL Management page (DataTable, filters, CRUD, bulk upload) | Epic 1 | Backend Lead | Sprint 1 scaffold |
| Implement URL Detail page (versions, changes, diffs) | Epic 1 | Backend Dev | Sprint 1 scaffold |
| Implement Change Review page (diff viewer, approve/reject, relocation) | Epic 1 | Backend Lead | Sprint 1 scaffold |
| Implement provider-agnostic OIDC auth module | Epic 2 | Backend Lead | None |
| Implement Cognito adapter and BFF session management | Epic 2 | Backend Lead | OIDC module |
| Configure CORS for frontend origin | Epic 2 | Backend Lead | OIDC module |
| Implement `s3_storage.py` and update PDF processing pipeline | Epic 4 | Backend Dev | None |
| Create S3 bucket with lifecycle rules | Epic 4 | Backend Dev | None |
| Add S3 columns to `pdf_versions` table | Epic 4 | Backend Dev | None |

### Sprint 3 (Weeks 5-6): Parity Completion + Evaluations

| Task | Epic | Owner | Dependencies |
| --- | --- | --- | --- |
| Implement Triage, Search, Metrics, Audit, Categories pages | Epic 1 | Backend Lead + Dev | Sprint 2 pages |
| Implement SSE monitoring progress (`useMonitoringStream` hook) | Epic 1 | Backend Dev | Backend SSE endpoint |
| Implement global command palette (Cmd+K) | Epic 1 | Backend Dev | Page routes defined |
| Implement `opensearch_search.py` and migrate search API | Epic 3 | Backend Dev | Sprint 1 indexer |
| Run one-time re-index of existing PDF versions | Epic 3 | Backend Dev | Search service complete |
| Rename `kendra_*` DB columns to `opensearch_*` | Epic 3 | Backend Dev | Search validation |
| Run BDA evaluation (BDA vs Textract+Claude on test dataset) | Epic 5 | Backend Lead | Evaluation dataset ready |
| Implement `llm_client.py` abstraction | Epic 6 | Backend Dev | None |
| Evaluate 3+ models for extraction task | Epic 6 | Backend Dev | `llm_client.py` |

### Sprint 4 (Weeks 7-8): Integration, Testing, Demo Prep

| Task | Epic | Owner | Dependencies |
| --- | --- | --- | --- |
| Integration testing: frontend against live backend API | Epic 1+2 | Full team | All pages + auth |
| Accessibility audit (Axe/Lighthouse) and fixes | Epic 1 | Backend Dev | All pages |
| Performance audit (Lighthouse, bundle analysis) and optimization | Epic 1 | Backend Dev | All pages |
| Deploy frontend to staging (current EKS or Amplify prototype) | Epic 1+7 | Infrastructure Lead | Frontend build passing |
| Deploy backend with updated auth to staging | Epic 2 | Backend Lead | Auth tests passing |
| Publish BDA evaluation report | Epic 5 | Backend Lead | Evaluation complete |
| Publish model evaluation report | Epic 6 | Backend Dev | Evaluations complete |
| SteerCo demo preparation | All | Tech Lead | Staging deployment |

### Q3 2026 — Post-v3.1

| Item | Priority | Status | Dependencies |
| --- | --- | --- | --- |
| BDA rollout (if evaluation positive) | P1 | Pending evaluation | Epic 5 report |
| Nova model rollout | P1 | Pending evaluation | Epic 6 report |
| Amplify/App Runner migration (if evaluation positive) | P2 | Pending evaluation | Epic 7 prototypes |
| Okta adapter implementation (when Okta is available) | P1 | Blocked | Company Okta rollout |

### Q4 2026 — v3.2 (Tentative)

| Item | Priority | Status |
| --- | --- | --- |
| Bedrock Knowledge Bases (chat/Q&A over documents) | P2 | Future |
| Agent Core integration (Forms Workflow automation) | P2 | Future |
| Court Rules monitoring platform (shared infrastructure) | P2 | Future |

### Epic Dependency Graph

```
Epic 1 (UI Rebuild) ─────────────────────────────────────────────────────┐
    │                                                                     │
    │ (frontend needs auth)                                               │
    ▼                                                                     │
Epic 2 (Auth) ────────────────────────────────────────────────────────────┤
                                                                          │
Epic 3 (OpenSearch) ──── [parallel, no dependencies] ─────────────────────┤
                                                                          │
Epic 4 (S3 Storage) ──── [parallel, no dependencies] ──────┐             │
                                                            │             │
                                                            ▼             │
Epic 5 (BDA Eval) ──── [needs S3 for PDF access] ──────────┤             │
                                                            │             │
Epic 6 (LLM Strategy) ── [parallel, no dependencies] ──────┤             │
                                                            │             │
                                                            ▼             ▼
Epic 7 (Deployment) ──── [needs frontend + backend] ───────────────────────
                                                            │
Epic 8 (Future) ──── [needs OpenSearch + S3] ──── Q4 2026+  │
```

**Key insight:** Epics 1, 3, 4, and 6 can all start in parallel on day one. This is the divide-and-conquer strategy: assign different team members to different epics and work simultaneously.

---

## Section 14: Development Tooling and DX

### Package Manager

**Tool:** pnpm

**Why:** Faster installs than npm, disk-efficient (shared content-addressable store), strict dependency resolution (prevents phantom dependencies), native workspace support if we need monorepo later.

### Linting and Formatting

| Tool | Purpose | Config File |
| --- | --- | --- |
| ESLint | JavaScript/TypeScript linting | `.eslintrc.js` or `eslint.config.mjs` |
| Prettier | Code formatting | `.prettierrc` |
| Tailwind IntelliSense | Tailwind class autocomplete/validation | VS Code extension |

### Git Hooks and Commit Quality

| Tool | Purpose | Config File |
| --- | --- | --- |
| Husky | Git hooks manager | `.husky/` |
| lint-staged | Run linters on staged files only | `.lintstagedrc` |
| Commitlint | Enforce conventional commit messages | `commitlint.config.js` |

**Conventional commit format:**

```
type(scope): description

feat(urls): add bulk upload progress indicator
fix(auth): handle session cookie expiration gracefully
chore(deps): update TanStack Query to v5.28
```

### Recommended VS Code Extensions

| Extension | Purpose |
| --- | --- |
| Tailwind CSS IntelliSense | Autocomplete, linting, hover preview for Tailwind classes |
| ESLint | Inline lint errors and auto-fix |
| Prettier | Format on save |
| TypeScript + JavaScript | Language support (built-in, ensure latest) |
| GitLens | Git blame, history, authorship |
| Error Lens | Inline error/warning display |
| Radix UI Snippets | Component scaffolding (optional) |

### Package Scripts

```json
{
  "scripts": {
    "dev": "next dev --turbo",
    "build": "next build",
    "start": "next start",
    "lint": "next lint && tsc --noEmit",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest",
    "test:e2e": "playwright test",
    "test:coverage": "vitest --coverage",
    "analyze": "ANALYZE=true next build"
  }
}
```

---

## Section 15: Appendices

### Appendix A: Frontend Code Examples

### SSE Monitoring Progress Hook

```tsx
// features/monitoring/hooks/use-monitoring-stream.ts
import { useEffect, useState, useCallback, useRef } from "react";

interface MonitoringProgress {
  total: number;
  completed: number;
  current_url: string | null;
  status: "idle" | "running" | "completed" | "error";
  errors: string[];
}

export function useMonitoringStream() {
  const [progress, setProgress] = useState<MonitoringProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource("/api/monitor/progress/stream", {
      withCredentials: true, // Send cookies for BFF auth
    });

    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as MonitoringProgress;
        setProgress(data);
      } catch {
        console.error("Failed to parse SSE message:", event.data);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
      eventSourceRef.current = null;

      // Reconnect after 5 seconds
      setTimeout(() => {
        connect();
      }, 5000);
    };

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  return { progress, isConnected, connect, disconnect };
}
```

### URL Status Badge Component

```tsx
// components/ui/url-status-badge.tsx
import { Badge } from "@/components/ui/badge";
import { cva, type VariantProps } from "class-variance-authority";

const statusVariants = cva("", {
  variants: {
    status: {
      active:
        "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
      changed:
        "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
      error: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
      archived:
        "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
      new: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    },
  },
  defaultVariants: {
    status: "active",
  },
});

type StatusType = "active" | "changed" | "error" | "archived" | "new";

interface URLStatusBadgeProps extends VariantProps<typeof statusVariants> {
  status: StatusType;
}

export function URLStatusBadge({ status }: URLStatusBadgeProps) {
  return (
    <Badge className={statusVariants({ status })}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
```

### Appendix B: Environment Variables Reference

### Backend Configuration

| Variable | Description | Required | Default | Epic |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | Yes | — | Existing |
| `SECRET_KEY` | Application secret key | Yes | — | Existing |
| `OIDC_PROVIDER` | Identity provider (`cognito`, `okta`) | Yes | `cognito` | Epic 2 |
| `OIDC_ISSUER` | OIDC issuer URL | Yes | — | Epic 2 |
| `OIDC_AUDIENCE` | OIDC audience/client ID | Yes | — | Epic 2 |
| `OIDC_CLIENT_SECRET` | Client secret for token exchange | Yes | — | Epic 2 |
| `AUTH_SESSION_COOKIE_NAME` | HttpOnly session cookie name | No | `url_monitor_session` | Epic 2 |
| `AUTH_SESSION_TTL_SECONDS` | Session lifetime in seconds | No | `3600` | Epic 2 |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s) for CORS | Yes | — | Epic 2 |
| `OPENSEARCH_ENDPOINT` | OpenSearch Serverless endpoint | Yes (when enabled) | — | Epic 3 |
| `OPENSEARCH_COLLECTION_NAME` | Collection name | Yes (when enabled) | — | Epic 3 |
| `OPENSEARCH_INDEX_NAME` | Index name | No | `court-forms` | Epic 3 |
| `OPENSEARCH_ENABLED` | Feature flag | No | `false` | Epic 3 |
| `S3_PDF_BUCKET` | S3 bucket for PDF storage | Yes (when enabled) | — | Epic 4 |
| `S3_PDF_PREFIX` | S3 key prefix | No | `url-monitor/` | Epic 4 |
| `S3_PDF_STORAGE_CLASS` | Default storage class | No | `STANDARD` | Epic 4 |
| `S3_ENABLED` | Feature flag | No | `false` | Epic 4 |
| `BDA_ENABLED` | Feature flag for BDA extraction | No | `false` | Epic 5 |
| `BDA_PROJECT_ARN` | BDA project ARN | Yes (when enabled) | — | Epic 5 |
| `BDA_BLUEPRINT_ARN` | BDA blueprint ARN | Yes (when enabled) | — | Epic 5 |
| `LLM_MODEL_PRIMARY` | Primary LLM model ID | No | `amazon.nova-pro-v1:0` | Epic 6 |
| `LLM_MODEL_FALLBACK` | Fallback LLM model ID | No | `anthropic.claude-3-sonnet` | Epic 6 |

### Frontend Configuration

| Variable | Description | Required |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend API base URL | Yes |
| `NEXT_PUBLIC_APP_NAME` | Application display name | No (default: “URL Monitor”) |

### Appendix C: Documentation Acceptance Checklist

Use this checklist to verify PRD alignment before sharing with the team:

- [ ]  All PRD variants reference v3.1 wording and aligned date/update intent
- [ ]  No target-state references to Vite as primary frontend platform
- [ ]  No recommendation that frontend should store JWTs by default
- [ ]  TanStack default + AG Grid trigger policy appears in all relevant sections
- [ ]  “Cognito now, Okta target” and “provider-agnostic OIDC” appear in architecture/security sections
- [ ]  UI workstream appears as first execution task in v3.1
- [ ]  `/api/*` and `/api/monitor/progress/stream` are explicitly preserved
- [ ]  No conflicting instructions across PRD variants or companion docs

### Appendix D: AWS Solutions Architect Recommendations

Key recommendations from the AWS SA meeting with Matul and Jordan (February 2026):

| Topic | Recommendation | Rationale |
| --- | --- | --- |
| **Search** | OpenSearch Serverless over Kendra | Lower cost at our volume; full control over index; vector search extensibility; no need for Kendra’s managed crawling features |
| **Extraction** | Evaluate BDA over Textract + Claude | Reduces two-step process to one step; better for standard form documents; blueprints for field definition |
| **LLM models** | Test Nova Pro and Nova Lite alongside Claude | Cost savings; “always test at least three models” before locking in |
| **Kendra crawling** | Not recommended for our use case | Our URLs are simple, direct PDF links; Lambda approach is simpler and cheaper |
| **Comprehend** | Not needed for this project | LLM prompts can handle classification/extraction; Comprehend adds cost without clear benefit here |
| **Deployment** | Explore App Runner and Amplify | Will connect us with specialists for deeper evaluation |
| **Agent Core** | Future consideration | Good fit for multi-step workflows; Strands framework for agent development; deploy on Agent Core runtime |
| **Knowledge Bases** | Future consideration | Managed RAG for document Q&A; requires S3 storage and OpenSearch as prerequisites |

### Appendix E: Glossary

| Term | Definition |
| --- | --- |
| **BDA** | Bedrock Document Automation — AWS service for unified document extraction (OCR + layout + field extraction in one call) |
| **BFF** | Backend For Frontend — Pattern where the backend manages auth sessions and issues cookies to the browser, keeping tokens server-side |
| **BM25** | Best Matching 25 — A ranking algorithm used by search engines for keyword-based text search |
| **CORS** | Cross-Origin Resource Sharing — HTTP header mechanism that allows a frontend on one origin to request resources from a backend on a different origin |
| **FWF** | FormsWorkflow — Aderant’s existing forms management system that URL Monitor syncs with |
| **IDP** | Intelligent Document Processing — AWS solutions for automated document understanding and extraction |
| **LLM** | Large Language Model — AI models used for text generation, extraction, and classification (e.g., Claude, Nova) |
| **NAMI Systems** | External vendor that provides document labeling/naming services for court forms |
| **OIDC** | OpenID Connect — An identity layer on top of OAuth 2.0 used for authentication |
| **RAG** | Retrieval-Augmented Generation — Pattern that combines search retrieval with LLM generation for grounded answers |
| **SSE** | Server-Sent Events — HTTP-based protocol for server-to-client real-time updates (one-way, lighter than WebSockets) |
| **shadcn/ui** | A component collection (not a library) that provides copy-paste React components built on Radix UI + Tailwind CSS |
| **Radix UI** | Unstyled, accessible React component primitives for building design systems |
| **TanStack Table** | Headless table library for React — provides sorting, filtering, pagination logic without imposing UI |
| **TanStack Query** | Server-state management library for React — handles caching, background refetch, and optimistic updates for API data |
| **Zustand** | Lightweight global state management library for React |
| **Turbopack** | Next.js’s Rust-based bundler for fast development builds |

### Appendix F: Document History

| Version | Date | Changes |
| --- | --- | --- |
| 3.1 | 2026-02-17 | Comprehensive rewrite: UI-first execution priority; Next.js App Router + shadcn/ui frontend stack (replaces Vite); provider-agnostic OIDC auth with BFF pattern (replaces SPA JWT); TanStack Table default with AG Grid escalation policy; OpenSearch Serverless migration; S3 PDF storage; BDA evaluation; Nova model strategy; deployment modernization evaluation; 8 prioritized epics with user stories and acceptance criteria; full API contract reference; risk register; sprint-level roadmap; AWS SA recommendations incorporated |
| 3.0 | 2026-02-16 | OpenSearch migration, frontend/backend split (Vite + Radix), Claude revision date extraction |
| 2.0 | 2026-02-09 | Added new features, enhanced functionality, batch download, state/category models |
| 1.0 | 2025-XX-XX | Initial PRD |