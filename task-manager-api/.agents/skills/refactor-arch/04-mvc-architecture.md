# 04 — MVC Architecture Guidelines

Reference file for Phase 3 of the refactor-arch skill. These guidelines are technology-agnostic. Apply them to whatever stack was detected in Phase 1.

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Target Directory Structure](#target-directory-structure)
3. [Layer Responsibilities](#layer-responsibilities)
4. [Config Module](#config-module)
5. [Centralized Error Handling](#centralized-error-handling)
6. [Entry Point / Composition Root](#entry-point--composition-root)
7. [Dependency Rules](#dependency-rules)

---

## Core Principles

**Single Responsibility**: Each file should answer one question — "What does this do?" — with a one-sentence answer. If the answer requires "and", the file is doing too much.

**Dependency Direction**: Dependencies flow inward only. The HTTP layer depends on controllers. Controllers depend on models. Models depend on the database. Nothing in a lower layer imports from a higher layer.

**No Cross-Layer Leakage**:
- HTTP objects (request, response, headers, status codes) must never appear in controllers or models
- Raw database queries must never appear in route handlers or controllers
- Business rules must never appear in route handlers or models

**Testability**: Each layer should be independently testable by mocking the layer it depends on.

**Fail Fast on Configuration**: The application should refuse to start if required environment variables are missing, rather than failing at runtime during a request.

---

## Target Directory Structure

The exact file and directory names should match the conventions of the detected language and framework, but the organizational pattern below is the target for every stack:

```
project/
├── <entry_point>           # Application entry — wires everything, zero business logic
├── config.<ext>            # All settings loaded from environment variables
├── <dependency_file>       # e.g., requirements.txt, package.json, pom.xml
├── .env.example            # Documents required environment variables (no real values)
│
├── models/                 # Data access layer — one file per domain entity
│   ├── <entity_1>.<ext>    # All queries and data access for entity 1
│   ├── <entity_2>.<ext>    # All queries and data access for entity 2
│   └── database.<ext>      # Database connection factory / session management
│
├── controllers/            # Business logic layer — one file per domain area
│   ├── <entity_1>_controller.<ext>
│   ├── <entity_2>_controller.<ext>
│   └── <entity_3>_controller.<ext>
│
├── routes/                 # HTTP interface layer — one file per route group
│   ├── <entity_1>_routes.<ext>
│   ├── <entity_2>_routes.<ext>
│   └── <entity_3>_routes.<ext>
│
├── middleware/             # Cross-cutting concerns
│   ├── auth.<ext>          # Authentication / authorization verification
│   └── error_handler.<ext> # Centralized exception-to-response translation
│
└── utils/                  # Shared helpers used by multiple layers
    └── security.<ext>      # Password hashing, token utilities
```

### Mapping the legacy codebase to this structure

When refactoring, create a mapping before writing any code:

| Existing file / function | New location | Reason |
|--------------------------|--------------|--------|
| `app.py` route definitions | `routes/` | HTTP interface only |
| `controllers.py` validation logic | `controllers/` | Business rules |
| `models.py` DB queries | `models/` | Data access only |
| Hardcoded config in `app.py` | `config.<ext>` | Centralized settings |
| Scattered try/except blocks | `middleware/error_handler.<ext>` | Centralized errors |

---

## Layer Responsibilities

### Models Layer

**Owns**: All interaction with the database.

**Allowed to**:
- Execute queries using parameterized statements only
- Map database rows to plain data objects (dicts, structs, records)
- Handle database-level errors (connection failures, constraint violations)
- Define schemas or ORM mappings

**Not allowed to**:
- Import anything from routes or controllers
- Access HTTP request or response objects
- Apply business rules or contain conditional logic beyond query construction
- Trigger notifications, emails, or any side effects

**Guiding question**: "Does this function know about the database? Nothing else." If a model function checks a business rule (e.g., "is the stock sufficient?"), move that check to the controller.

---

### Controllers Layer

**Owns**: Business logic and orchestration.

**Allowed to**:
- Call model functions to read and write data
- Apply business rules: validate inputs against business invariants, enforce state machine transitions, perform calculations
- Orchestrate multiple model calls in a single operation
- Trigger side effects like notifications — or delegate to a dedicated service module
- Return plain data objects — never HTTP response objects

**Not allowed to**:
- Import or use HTTP request/response objects from the framework
- Execute raw database queries directly
- Know about HTTP status codes or response format
- Call other controllers directly (share a model or utility instead)

**Guiding question**: "Does this function know about business rules? Nothing about HTTP, nothing about SQL." If a controller function constructs a raw query, move that query to the model.

---

### Routes Layer

**Owns**: The HTTP interface.

**Allowed to**:
- Parse request body, query parameters, path parameters, and headers
- Call exactly one controller function per endpoint handler
- Format the controller's return value into an HTTP response (status code + body)
- Apply middleware (authentication, rate limiting, logging)
- Return appropriate HTTP error codes for HTTP-level failures (missing field → 400, not found → 404)

**Not allowed to**:
- Contain business logic or data calculations
- Execute database queries directly
- Know about model internals
- Branch on data values for business reasons (only on HTTP concerns like missing required fields)

**Guiding question**: "Does this function know about HTTP? Nothing about business rules, nothing about SQL."

---

## Config Module

**Purpose**: One place to define all configuration values. Prevents credentials and settings from being scattered across the codebase.

**Rules**:
1. Read all values from environment variables — never hardcode credentials or secrets
2. Provide sensible defaults only for non-sensitive settings (ports, timeouts, feature flags)
3. Never provide a default for secrets — fail explicitly if they are missing
4. Document every required and optional variable in `.env.example` with a brief comment
5. Call a `validate()` function at startup before the application begins accepting requests

**Structure of the config module**:

```
config.<ext>
├── Load all values from environment variables
├── Group by category: database, security, application, external services
├── Expose a validate() function that raises an error if required vars are missing
└── Export the config as a single object or class
```

**`.env.example` structure**:

```
# === Required — the application will not start without these ===
SECRET_KEY=

# === Optional — shown with their default values ===
DATABASE_URL=app.db
DEBUG=false
BCRYPT_ROUNDS=12
PORT=5000
```

---

## Centralized Error Handling

**Purpose**: Translate all exceptions into appropriate HTTP responses in one place. Eliminates the pattern of try/except + error response formatting scattered throughout every route handler.

**How it works**:
- Register a global error handler with the framework (most web frameworks support this)
- Route handlers propagate exceptions upward instead of catching them locally
- The error handler categorizes the exception and returns the correct HTTP status and body
- All error logging happens in one place with full stack traces

**Error handler responsibilities**:

| Situation | HTTP Status | Response body |
|-----------|-------------|---------------|
| Validation failure (known business error) | 400 | `{"erro": "<message>", "sucesso": false}` |
| Resource not found | 404 | `{"erro": "Recurso não encontrado", "sucesso": false}` |
| Not authenticated | 401 | `{"erro": "Não autorizado", "sucesso": false}` |
| Not authorized | 403 | `{"erro": "Acesso negado", "sucesso": false}` |
| Unhandled exception | 500 | `{"erro": "Erro interno do servidor", "sucesso": false}` |

**Important**: For 500 errors, log the full exception with stack trace using a structured logger. For 4xx errors, log at INFO or DEBUG level. Never expose internal error messages to the client in production.

**After adding a centralized error handler**, route handlers become much simpler — they only need to parse the request, call the controller, and return a response. They do not need try/except blocks for most cases.

---

## Entry Point / Composition Root

**Purpose**: Wire all modules together and start the application. This file should contain zero business logic.

**Responsibilities**:
1. Load and validate configuration
2. Initialize the framework/application object
3. Register all route modules
4. Register middleware (auth, error handler, logging, CORS)
5. Start the server (or export the app for a WSGI/ASGI server)

**What must NOT be in the entry point**:
- Business logic of any kind
- Database queries
- Request/response handling beyond middleware registration
- Hardcoded configuration values
- `print` or ad-hoc debug output

**Pattern**: The entry point should read like a table of contents for the application. Someone new to the codebase should be able to understand the entire application structure just by reading this file.

---

## Dependency Rules

The diagram below defines which layers may import from which. Arrows point from dependent to dependency (A → B means A may import from B).

```
                     ┌──────────────┐
                     │    Routes    │  HTTP interface
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Controllers │  Business logic
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Models    │  Data access
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Database   │  Connection / driver
                     └──────────────┘

 ┌────────┐    read-only    All layers
 │ Config │ ◄────────────── may read config
 └────────┘

 ┌────────┐    imported by  Routes layer only
 │  Auth  │ ◄────────────── (via middleware decorator)
 └────────┘

 ┌────────┐    imported by  Entry point registers it;
 │ Error  │ ◄────────────── exceptions propagate up to it
 │Handler │
 └────────┘

 ┌────────┐    imported by  Any layer may use shared helpers
 │ Utils  │ ◄──────────────
 └────────┘
```

**Violations to identify and fix during refactoring**:

| Violation | Fix |
|-----------|-----|
| A model function imports from a controller or route | Invert: pass data as parameters instead |
| A route handler calls a model function directly | Add a controller function in between |
| A controller imports the HTTP request object | Move request parsing to the route handler; pass parsed values to the controller |
| Business logic lives in `app.py` / entry point | Move to the appropriate controller |
| A model function checks a business invariant (e.g., stock availability) | Move the check to the controller; the model only fetches data |
| Config values hardcoded anywhere outside `config.<ext>` | Move to config module and read from environment |
