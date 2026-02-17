# API Contracts — Single Source of Truth

> Every agent must read this file before making changes to any endpoint, schema, or data model.
> Update this file whenever API contracts or DB schema change.
> This file is generated during **Phase 1** (Contracts First) and maintained throughout the project.

---

## Endpoints

<!-- List every endpoint with method, path, auth requirement, and one-line description -->

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| | | | |

---

## Data Models

<!-- Define every entity with fields, types, and constraints -->
<!-- Note: These will become Pydantic schemas (OrderCreate, OrderResponse, OrderUpdate) and SQLAlchemy models -->

### [Model Name]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | uuid | yes | Primary key |
| created_at | timestamp | yes | Auto-set on creation |
| updated_at | timestamp | yes | Auto-set on update |
| | | | |

---

## Business Rules

<!-- List business rules that affect endpoint behaviour -->

1. [Rule description — e.g. "An order cannot be cancelled after it has been shipped"]

---

## Auth Flows

<!-- Describe authentication and authorization patterns -->

- **Auth type**: [e.g. JWT Bearer token]
- **Token source**: [e.g. Authorization header]
- **Roles/scopes**: [e.g. admin, user, read-only]
- **Public endpoints**: [list any endpoints that don't require auth]

---

## Error Shapes

<!-- Define the standard error response format -->
<!-- FastAPI uses HTTPException with detail field. Format below matches FastAPI conventions. -->

All error responses follow this envelope:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": []
  }
}
```

### Error Codes

| Code | HTTP Status | When |
|------|-------------|------|
| VALIDATION_ERROR | 400 | Request body fails schema validation |
| UNAUTHORIZED | 401 | Missing or invalid auth token |
| FORBIDDEN | 403 | Valid auth but insufficient permissions |
| NOT_FOUND | 404 | Resource does not exist |
| CONFLICT | 409 | Duplicate or state violation |
| INTERNAL_ERROR | 500 | Unhandled server error |

---

## Edge Cases

<!-- List edge cases and how they should be handled -->

1. [Edge case — e.g. "What happens if a user creates two orders simultaneously?"]

---

## DB Schema Summary

<!-- Maintained alongside migrations — update when schema changes -->

### Tables

| Table | Description | Key Indexes |
|-------|-------------|-------------|
| | | |

---

*Last updated: [date]*
