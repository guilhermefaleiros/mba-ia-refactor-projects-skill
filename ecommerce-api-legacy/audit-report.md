# Security & Quality Audit Report

## Project Metadata
| Field         | Value                        |
|---------------|------------------------------|
| Project       | ecommerce-api-legacy         |
| Language      | JavaScript (Node.js)         |
| Framework     | Express.js                   |
| Database      | SQLite (raw queries)         |
| Files scanned | 3                            |
| LOC           | ~180                         |
| Scan date     | 2026-04-21                   |

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 5     |
| HIGH     | 6     |
| MEDIUM   | 4     |
| LOW      | 5     |
| **TOTAL**| **20**|

Critical risks include hardcoded credentials and insecure/custom password hashing. The codebase also has missing authentication on sensitive endpoints, business logic embedded in HTTP handlers, and N+1 query patterns in the admin report flow. Overall production risk is high.

---

## Findings

### CRITICAL

---

#### [C1] Hardcoded Credentials

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | CRITICAL                         |
| Pattern        | P02 - Hardcoded Credentials      |
| Location       | `src/utils.js` lines 3-3         |

**Description:**
Line 3 defines `dbPass: "senha_super_secreta_prod_123"` directly in source code.

**Impact:**
Credentials committed to source control are permanently exposed. Anyone with read access to the code can authenticate as the system.

**Recommendation:**
Move secrets to `process.env` and remove real fallback values. Document required variables in `.env.example`.

---

#### [C2] Hardcoded Credentials

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | CRITICAL                         |
| Pattern        | P02 - Hardcoded Credentials      |
| Location       | `src/utils.js` lines 4-4         |

**Description:**
Line 4 defines `paymentGatewayKey: "pk_live_1234567890abcdef"` in code.

**Impact:**
Credentials committed to source control are permanently exposed. Anyone with read access to the code can authenticate as the system.

**Recommendation:**
Load gateway keys from `process.env.PAYMENT_GATEWAY_KEY`; never keep real keys in the repository.

---

#### [C3] Hardcoded Credentials

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | CRITICAL                         |
| Pattern        | P02 - Hardcoded Credentials      |
| Location       | `src/AppManager.js` lines 18-18  |

**Description:**
Database seed inserts a user with a literal password `'123'` on line 18.

**Impact:**
Credentials committed to source control are permanently exposed. Anyone with read access to the code can authenticate as the system.

**Recommendation:**
Do not ship predictable default credentials; use secure seeded hashes and environment-driven secrets.

---

#### [C4] Hardcoded Credentials

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | CRITICAL                         |
| Pattern        | P02 - Hardcoded Credentials      |
| Location       | `src/AppManager.js` lines 68-68  |

**Description:**
Line 68 uses a hardcoded password fallback `p || "123456"` before hashing.

**Impact:**
Credentials committed to source control are permanently exposed. Anyone with read access to the code can authenticate as the system.

**Recommendation:**
Remove fixed password fallback and enforce explicit valid password input.

---

#### [C5] Insecure Hashing

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | CRITICAL                         |
| Pattern        | P03 - Insecure Hashing           |
| Location       | `src/utils.js` lines 17-22       |

**Description:**
`badCrypto` "hashes" passwords by repeating `Buffer.from(...).toString('base64')`, which is reversible encoding, not secure password hashing.

**Impact:**
Weak/custom hashing makes password recovery feasible; stolen credential data becomes quickly compromisable.

**Recommendation:**
Replace with `bcrypt` or `argon2` using salt and cost factor; remove `badCrypto` entirely.

---

### HIGH

---

#### [H1] God Class / God File

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P04 - God Class / God File       |
| Location       | `src/AppManager.js` lines 1-138  |

**Description:**
`AppManager.js` mixes DB initialization, seed data, HTTP route definitions, business logic, and persistence concerns in one module.

**Impact:**
High coupling makes testing, maintenance, and safe changes significantly harder.

**Recommendation:**
Split by layers (routes/controllers/models/config), with one clear responsibility per file.

---

#### [H2] Business Logic in Routes/Controllers

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P05 - Business Logic in Routes/Controllers |
| Location       | `src/AppManager.js` lines 28-77  |

**Description:**
`/api/checkout` contains payment decision logic, conditional user creation, and enrollment orchestration inside the HTTP handler.

**Impact:**
Business rules become tightly coupled to the web layer and are not reusable/testable in isolation.

**Recommendation:**
Extract checkout flow into controller/service functions; route should only parse request and delegate.

---

#### [H3] Business Logic in Routes/Controllers

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P05 - Business Logic in Routes/Controllers |
| Location       | `src/AppManager.js` lines 80-129 |

**Description:**
`/api/admin/financial-report` computes revenue and aggregates students with nested loops and DB calls directly in the route handler.

**Impact:**
Embedding business rules in endpoints increases regression risk and reduces maintainability.

**Recommendation:**
Move report composition logic into dedicated controller/service layer.

---

#### [H4] Missing Authentication / Authorization

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P06 - Missing Authentication / Authorization |
| Location       | `src/AppManager.js` lines 80-129 |

**Description:**
Admin endpoint `/api/admin/financial-report` has no authentication or authorization guard.

**Impact:**
Unprotected admin endpoints can expose sensitive operational data.

**Recommendation:**
Apply authentication middleware and role-based authorization for admin-only routes.

---

#### [H5] Missing Authentication / Authorization

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P06 - Missing Authentication / Authorization |
| Location       | `src/AppManager.js` lines 131-137 |

**Description:**
`DELETE /api/users/:id` performs destructive action without identity or permission checks.

**Impact:**
Unauthenticated users can execute destructive operations.

**Recommendation:**
Require authentication plus owner/admin authorization before delete operations.

---

#### [H6] Missing Authentication / Authorization

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | HIGH                             |
| Pattern        | P06 - Missing Authentication / Authorization |
| Location       | `src/AppManager.js` lines 28-77  |

**Description:**
`POST /api/checkout` executes account/payment/enrollment operations without auth controls (verify manually).

**Impact:**
Sensitive workflows may be abused by unauthenticated clients.

**Recommendation:**
Define public/private endpoint policy and protect account/data-changing operations with auth middleware.

---

### MEDIUM

---

#### [M1] N+1 Queries

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | MEDIUM                           |
| Pattern        | P08 - N+1 Queries                |
| Location       | `src/AppManager.js` lines 89-107 |

**Description:**
For each course, it fetches enrollments; for each enrollment, it runs separate user and payment queries.

**Impact:**
As data grows, one request can trigger hundreds/thousands of DB round trips.

**Recommendation:**
Replace with joined queries (or batch queries with `IN (...)`) for report generation.

---

#### [M2] Code Duplication

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | MEDIUM                           |
| Pattern        | P09 - Code Duplication           |
| Location       | `src/AppManager.js` lines 38-70  |

**Description:**
Error response handling (`res.status(...).send(...)`) is repeated across multiple nested callbacks.

**Impact:**
Changing error behavior requires edits in multiple places, increasing inconsistency risk.

**Recommendation:**
Centralize error handling and extract shared flow into controllers/helpers.

---

#### [M3] Bare Except / Silent Errors

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | MEDIUM                           |
| Pattern        | P11 - Bare Except / Silent Errors |
| Location       | `src/AppManager.js` lines 57-61  |

**Description:**
The `audit_logs` insert callback ignores `err` and always returns success (`res.status(200)...`) (verify manually).

**Impact:**
Real failures can be hidden, reducing observability and transactional consistency.

**Recommendation:**
Handle DB errors explicitly, log with context, and return proper error responses.

---

#### [M4] Bare Except / Silent Errors

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | MEDIUM                           |
| Pattern        | P11 - Bare Except / Silent Errors |
| Location       | `src/AppManager.js` lines 133-136 |

**Description:**
User delete callback ignores `err` and always returns success (verify manually).

**Impact:**
Clients may receive success responses when operations fail.

**Recommendation:**
Check DB errors before responding and use centralized error middleware.

---

### LOW

---

#### [L1] Print Statements as Logging

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | LOW                              |
| Pattern        | P12 - Print Statements as Logging |
| Location       | `src/app.js` lines 13-13         |

**Description:**
`console.log` is used for production startup logging.

**Impact:**
Logs are unstructured and lack level/routing controls for observability.

**Recommendation:**
Use a structured logger (`pino`/`winston`) with levels and consistent formatting.

---

#### [L2] Print Statements as Logging

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | LOW                              |
| Pattern        | P12 - Print Statements as Logging |
| Location       | `src/AppManager.js` lines 45-45  |

**Description:**
`console.log` prints card data and gateway key during checkout flow.

**Impact:**
Besides unstructured logs, this increases sensitive data leakage risk in logs.

**Recommendation:**
Remove sensitive fields from logs and adopt structured logging with redaction.

---

#### [L3] Print Statements as Logging

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | LOW                              |
| Pattern        | P12 - Print Statements as Logging |
| Location       | `src/utils.js` lines 13-13       |

**Description:**
`console.log` is used in `logAndCache` for cache events.

**Impact:**
Non-standard logging harms monitoring and alerting quality.

**Recommendation:**
Replace with centralized logger and proper log levels (`debug/info/error`).

---

#### [L4] Dead Code

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | LOW                              |
| Pattern        | P13 - Dead Code                  |
| Location       | `src/utils.js` lines 10-10       |

**Description:**
`totalRevenue` is declared/exported but not effectively used by the application.

**Impact:**
Dead code increases cognitive load and suggests non-existent behavior.

**Recommendation:**
Remove dead code or implement a justified real use case.

---

#### [L5] Magic Numbers / Magic Strings

| Field          | Value                            |
|----------------|----------------------------------|
| Severity       | LOW                              |
| Pattern        | P14 - Magic Numbers / Magic Strings |
| Location       | `src/AppManager.js` lines 46-46  |

**Description:**
Payment approval rule uses literal values `cc.startsWith("4") ? "PAID" : "DENIED"` without named constants or explanation.

**Impact:**
Business rules are opaque and error-prone when requirements change.

**Recommendation:**
Extract named constants/enums and document payment decision policy.

---

## Footer

**Total findings: 20** (5 critical / 6 high / 4 medium / 5 low)

**Priority action plan:**
1. Fix all CRITICAL findings before deploying to any environment
2. Fix all HIGH findings before accepting user traffic
3. Schedule MEDIUM findings for the next sprint
4. Address LOW findings during regular maintenance
