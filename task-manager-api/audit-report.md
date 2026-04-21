# Security & Quality Audit Report

## Project Metadata
| Field         | Value                       |
|---------------|-----------------------------|
| Project       | task-manager-api            |
| Language      | Python 3                    |
| Framework     | Flask                       |
| Database      | SQLite via Flask-SQLAlchemy |
| Files scanned | 15                          |
| LOC           | ~968                        |
| Scan date     | 2026-04-21                  |

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 4     |
| HIGH     | 8     |
| MEDIUM   | 10    |
| LOW      | 7     |
| **TOTAL**| **29** |

The app has multiple critical security issues: hardcoded secrets/credentials and MD5 password hashing. It also lacks auth controls, returns sensitive data, and mixes business logic directly into route handlers, which keeps the code brittle and hard to secure.

---

## Findings

### CRITICAL

---

#### [C1] Hardcoded Credentials

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | CRITICAL                           |
| Pattern        | P02 — Hardcoded Credentials        |
| Location       | `app.py` lines 11–13               |

**Description:**
`SECRET_KEY` is hardcoded as `'super-secret-key-123'` in application config.

**Impact:**
Credentials committed to source control are permanently exposed.

**Recommendation:**
Apply Playbook P2: move secrets to environment variables and never use hardcoded fallback values.

---

#### [C2] Hardcoded Credentials

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | CRITICAL                           |
| Pattern        | P02 — Hardcoded Credentials        |
| Location       | `services/notification_service.py` lines 7–10 |

**Description:**
SMTP credentials are embedded directly in the service (`email_user` and `email_password`).

**Impact:**
Anyone with code access can reuse the mail account.

**Recommendation:**
Apply Playbook P2: read SMTP credentials from environment variables or a secrets manager.

---

#### [C3] Hardcoded Credentials (verify manually)

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | CRITICAL                           |
| Pattern        | P02 — Hardcoded Credentials        |
| Location       | `seed.py` lines 16–35              |

**Description:**
Seed data hardcodes sample user passwords (`'1234'`, `'abcd'`, `'pass'`) for created accounts.

**Impact:**
Fixture credentials are exposed in source and can be reused against seeded environments.

**Recommendation:**
Move demo credentials out of source or generate them dynamically; document them separately if they must exist.

---

#### [C4] Insecure Hashing

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | CRITICAL                           |
| Pattern        | P03 — Insecure Hashing             |
| Location       | `models/user.py` lines 27–32       |

**Description:**
Passwords are hashed and verified with `hashlib.md5(...)`.

**Impact:**
MD5 is cryptographically broken for passwords.

**Recommendation:**
Apply Playbook P3: switch to bcrypt or argon2 for password hashing.

---

### HIGH

---

#### [H1] God Class / God File

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P04 — God Class / God File         |
| Location       | `utils/helpers.py` lines 1–117     |

**Description:**
This module mixes validation, parsing, logging, formatting, task normalization, and constants in one utility dump.

**Impact:**
God files are hard to test, hard to reuse, and tend to accumulate more coupled logic.

**Recommendation:**
Split helpers by responsibility and move business rules into dedicated controller/service code.

---

#### [H2] Business Logic in Routes/Controllers

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P05 — Business Logic in Routes/Controllers |
| Location       | `routes/task_routes.py` lines 11–300 |

**Description:**
Task handlers do validation, overdue calculation, filtering, relationship lookups, and stats aggregation directly in route functions.

**Impact:**
Business rules become tied to HTTP handlers and are harder to test or reuse.

**Recommendation:**
Apply Playbook P5: move orchestration and rules into controllers/services, leaving routes for request/response plumbing.

---

#### [H3] Business Logic in Routes/Controllers

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P05 — Business Logic in Routes/Controllers |
| Location       | `routes/user_routes.py` lines 10–212 |

**Description:**
User endpoints mix validation, password handling, duplicate checks, task deletion, and login flow in route handlers.

**Impact:**
HTTP code and business rules are coupled together, making changes risky.

**Recommendation:**
Extract a controller/service layer for user registration, updates, deletion, and authentication logic.

---

#### [H4] Business Logic in Routes/Controllers

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P05 — Business Logic in Routes/Controllers |
| Location       | `routes/report_routes.py` lines 12–224 |

**Description:**
Report and category handlers perform aggregation, business calculations, and write operations directly in the route file.

**Impact:**
Reporting logic cannot be reused cleanly and is difficult to isolate in tests.

**Recommendation:**
Move report generation and category management into dedicated controller/service functions.

---

#### [H5] Missing Authentication / Authorization

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P06 — Missing Authentication / Authorization |
| Location       | `routes/task_routes.py` lines 11–300 |

**Description:**
Task CRUD and search/stat endpoints have no visible auth guard.

**Impact:**
Unauthenticated users can read and modify task data.

**Recommendation:**
Add auth middleware and apply it to all non-public task endpoints.

---

#### [H6] Missing Authentication / Authorization

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P06 — Missing Authentication / Authorization |
| Location       | `routes/user_routes.py` lines 10–212 |

**Description:**
User listing, profile access, updates, deletion, and login flows are exposed without any auth check.

**Impact:**
Attackers can access or modify user data without proving identity.

**Recommendation:**
Protect user endpoints with authentication and authorization checks.

---

#### [H7] Missing Authentication / Authorization

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P06 — Missing Authentication / Authorization |
| Location       | `routes/report_routes.py` lines 12–224 |

**Description:**
Reports and category write endpoints are exposed without auth middleware.

**Impact:**
Anyone can read internal reports or mutate categories.

**Recommendation:**
Add middleware to require auth for reports and category management.

---

#### [H8] Sensitive Data Exposure

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P07 — Sensitive Data Exposure     |
| Location       | `models/user.py` lines 16–25       |

**Description:**
`to_dict()` returns the `password` field, and multiple endpoints reuse that serializer.

**Impact:**
Password hashes can be leaked in API responses.

**Recommendation:**
Whitelist returned fields and never serialize password data.

---

### MEDIUM

---

#### [M1] N+1 Queries

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P08 — N+1 Queries                  |
| Location       | `routes/task_routes.py` lines 14–59 |

**Description:**
`get_tasks()` loads all tasks, then queries each task’s user and category inside the loop.

**Impact:**
This creates one query per row and degrades quickly as task volume grows.

**Recommendation:**
Use joins or eager loading to fetch related records in one query.

---

#### [M2] N+1 Queries

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P08 — N+1 Queries                  |
| Location       | `routes/report_routes.py` lines 53–68 |

**Description:**
`summary_report()` loads all users and then queries tasks again for each user inside the loop.

**Impact:**
This scales poorly and amplifies report latency.

**Recommendation:**
Batch fetch task counts or aggregate with a grouped query.

---

#### [M3] N+1 Queries

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P08 — N+1 Queries                  |
| Location       | `routes/report_routes.py` lines 157–164 |

**Description:**
`get_categories()` performs a count query for every category inside a loop.

**Impact:**
Each category adds another database round-trip.

**Recommendation:**
Fetch category task counts with a grouped aggregate query.

---

#### [M4] Code Duplication

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P09 — Code Duplication             |
| Location       | `routes/task_routes.py` lines 85–214 |

**Description:**
Create and update handlers repeat the same title, status, priority, due date, and tag validation logic.

**Impact:**
Changes must be updated in multiple places, increasing drift risk.

**Recommendation:**
Extract shared task validation/parsing into a single helper or controller method.

---

#### [M5] Code Duplication

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P09 — Code Duplication             |
| Location       | `routes/user_routes.py` lines 42–132 |

**Description:**
Create and update user handlers duplicate email validation, password checks, and role validation.

**Impact:**
Validation rules can diverge across endpoints.

**Recommendation:**
Centralize user validation and password handling in one shared routine.

---

#### [M6] Bare Except / Silent Errors

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P11 — Bare Except / Silent Errors  |
| Location       | `routes/task_routes.py` lines 62–63, 137–138, 151–154, 204–205, 221–223, 236–238 |

**Description:**
Multiple task handlers catch all exceptions or swallow errors with generic 500 responses and prints.

**Impact:**
Bugs are hidden and error behavior becomes inconsistent.

**Recommendation:**
Catch specific exceptions, log them properly, and centralize error handling.

---

#### [M7] Bare Except / Silent Errors

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P11 — Bare Except / Silent Errors  |
| Location       | `routes/user_routes.py` lines 87–90, 130–132, 149–151 |

**Description:**
User handlers swallow exceptions and return generic responses.

**Impact:**
Failures are obscured and debugging becomes harder.

**Recommendation:**
Use specific exception handling and centralized error responses.

---

#### [M8] Bare Except / Silent Errors

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P11 — Bare Except / Silent Errors  |
| Location       | `routes/report_routes.py` lines 186–188, 207–209, 221–223 |

**Description:**
Category write handlers catch all exceptions and only return generic errors.

**Impact:**
Important failure details are lost.

**Recommendation:**
Raise or log the underlying exception through a shared error handler.

---

#### [M9] Bare Except / Silent Errors

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P11 — Bare Except / Silent Errors  |
| Location       | `utils/helpers.py` lines 44–50 |

**Description:**
`parse_date()` uses nested bare `except:` blocks and returns `None` on failure.

**Impact:**
Parsing errors are silently hidden.

**Recommendation:**
Catch specific parse errors and propagate a clear validation failure.

---

#### [M10] Bare Except / Silent Errors

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P11 — Bare Except / Silent Errors  |
| Location       | `services/notification_service.py` lines 23–25 |

**Description:**
Email send failures are caught broadly and reduced to a `False` return with printed output.

**Impact:**
Operational failures are hidden from the caller.

**Recommendation:**
Log the exception properly and surface the error through the service layer.

---

### LOW

---

#### [L1] Dead Code

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P13 — Dead Code                   |
| Location       | `routes/report_routes.py` lines 7–8 |

**Description:**
`format_date` and `calculate_percentage` are imported but never used.

**Impact:**
Unused imports add noise and mislead readers.

**Recommendation:**
Remove unused imports or wire them into the report logic.

---

#### [L2] Dead Code

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P13 — Dead Code                   |
| Location       | `utils/helpers.py` lines 9–117 |

**Description:**
Several helper functions and constants appear unused across the project.

**Impact:**
Dead helpers increase cognitive load and hide what is actually in use.

**Recommendation:**
Delete unused helpers or move them to the layer that consumes them.

---

#### [L3] Dead Code

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P13 — Dead Code                   |
| Location       | `models/task.py` lines 38–60 |

**Description:**
`validate_status()`, `validate_priority()`, and `is_overdue()` are defined on the model but not referenced anywhere else.

**Impact:**
Model methods that are never called create maintenance overhead.

**Recommendation:**
Remove them or move them into the code path that actually uses them.

---

#### [L4] Dead Code

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P13 — Dead Code                   |
| Location       | `models/user.py` lines 34–38 |

**Description:**
`is_admin()` is defined but not used anywhere in the app.

**Impact:**
Dead methods add clutter and suggest missing authorization wiring.

**Recommendation:**
Delete it or wire it into actual authorization checks.

---

#### [L5] Magic Numbers / Magic Strings

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P14 — Magic Numbers / Magic Strings |
| Location       | `routes/task_routes.py` lines 96–114, 166–184, 273–299 |

**Description:**
Task validation hardcodes title-length limits, priority range, and status strings in multiple handlers.

**Impact:**
Business thresholds are scattered and hard to update consistently.

**Recommendation:**
Move these values into named constants or config.

---

#### [L6] Magic Numbers / Magic Strings

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P14 — Magic Numbers / Magic Strings |
| Location       | `routes/user_routes.py` lines 52–78, 119–121, 207–210 |

**Description:**
User logic hardcodes allowed roles, minimum password length, and the fake token prefix.

**Impact:**
These values are opaque and repeated in-line.

**Recommendation:**
Extract them into constants and a real auth/token strategy.

---

#### [L7] Magic Numbers / Magic Strings

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P14 — Magic Numbers / Magic Strings |
| Location       | `routes/report_routes.py` lines 24–28, 45–46, 83–89, 129–151 |

**Description:**
Priority labels, seven-day windows, and priority thresholds are embedded directly in report logic.

**Impact:**
Reporting rules are harder to tune or reuse.

**Recommendation:**
Centralize reporting thresholds and status labels in named constants or config.

---

## Footer

**Total findings: 29** (4 critical / 8 high / 10 medium / 7 low)

**Priority action plan:**
1. Fix all CRITICAL findings before deploying to any environment
2. Fix all HIGH findings before accepting user traffic
3. Schedule MEDIUM findings for the next sprint
4. Address LOW findings during regular maintenance
