# 02 — Anti-Patterns Catalog

Reference file for Phase 2 of the refactor-arch skill. For each of the 14 patterns below, apply the detection signals to every source file and record all occurrences.

---

## How to use this catalog

For each pattern:
1. Apply the detection signals to scan source files
2. When a signal matches, record: **file path**, **line numbers**, **pattern name**, **severity**
3. Write a one-sentence description of the specific occurrence
4. Note the impact and recommended fix (use these verbatim in the audit report)

Severity levels: **CRITICAL** → **HIGH** → **MEDIUM** → **LOW**

---

## CRITICAL Patterns

---

### P01 — SQL Injection

**Severity:** CRITICAL

**Detection signals:**
- String concatenation used to build SQL queries: `"SELECT ... WHERE id = " + str(id)`
- f-string or `.format()` used inside a SQL string: `f"SELECT * FROM users WHERE name = '{name}'"`
- `%` string formatting inside SQL: `"SELECT * FROM t WHERE x = '%s'" % value` (without using DB-API parameterization)
- `cursor.execute()` called with a string that contains variable interpolation
- `db.query()` / `session.execute()` called with a concatenated string

**What is NOT a signal (avoid false positives):**
- `cursor.execute("SELECT * FROM t WHERE id = ?", (id,))` — this is safe, parameterized
- `cursor.execute("SELECT * FROM t WHERE id = %s", (id,))` — this is safe
- `text()` construct in SQLAlchemy with bound parameters

**Impact:** An attacker can manipulate the SQL query to bypass authentication, dump the entire database, modify or delete data, or execute administrative operations. This is the most exploited class of web vulnerability.

**Recommendation:** Replace all string-concatenated queries with parameterized queries using `?` (SQLite) or `%s` (PostgreSQL/MySQL) placeholders and pass values as a tuple to `cursor.execute()`.

---

### P02 — Hardcoded Credentials

**Severity:** CRITICAL

**Detection signals:**
- String literals assigned to variables named: `password`, `passwd`, `secret`, `secret_key`, `api_key`, `token`, `auth_token`, `db_password`, `private_key`
- Config dictionaries with literal string values for keys like `SECRET_KEY`, `DATABASE_URL`, `PASSWORD`
- Connection strings with credentials embedded: `"postgresql://user:password@host/db"`
- `os.environ.get("KEY", "fallback-literal-value")` where the fallback is a real credential

**Examples of positive signals:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PASSWORD = "admin123"
API_KEY = "sk-abc123xyz"
```

**Impact:** Credentials committed to source control are permanently exposed. Anyone with read access to the code — including CI systems, contractors, and public GitHub forks — can authenticate as the system.

**Recommendation:** Move all credentials to environment variables. Read them with `os.environ.get("KEY")` in Python or `process.env.KEY` in Node.js. Document required variables in `.env.example`. Never use a hardcoded fallback for secrets.

---

### P03 — Insecure Hashing

**Severity:** CRITICAL

**Detection signals:**
- `import hashlib` followed by `hashlib.md5(` or `hashlib.sha1(`
- `md5(password)` or `sha1(password)` calls
- Custom hash functions that XOR, rotate, or combine characters manually
- Passwords stored as plain hex strings without salt
- `base64.encode(password)` used as "hashing" (encoding is not hashing)
- Comparing passwords with `==` against a stored hash without a timing-safe comparison

**What is NOT a signal:**
- `hashlib.sha256()` or `hashlib.sha512()` used for file integrity checks (not passwords) — note as low risk
- `hashlib.sha256()` for HMAC or token generation — note as acceptable if not for passwords

**Impact:** MD5 and SHA1 are cryptographically broken for passwords. Rainbow tables and GPU cracking can reverse MD5 hashes at billions of guesses per second. Any stolen password database is fully recoverable.

**Recommendation:** Use `bcrypt` (`pip install bcrypt`) or `argon2-cffi` (`pip install argon2-cffi`) for password hashing. In Node.js: `bcrypt` or `argon2`. These algorithms are intentionally slow and include salting.

---

## HIGH Patterns

---

### P04 — God Class / God File

**Severity:** HIGH

**Detection signals:**
- A single file with more than ~300 lines that contains multiple unrelated responsibilities
- A class or module that handles: HTTP request parsing AND business logic AND database queries AND response formatting
- A file that exports 10+ unrelated functions
- Model files that contain route handlers, or route files that contain database queries
- A `utils.py` or `helpers.js` that has grown to contain half the application logic

**Measuring signals:**
- File LOC > 300 and contains functions from 3+ different responsibility categories
- A single class with > 15 methods spanning different concerns

**Impact:** God classes are the root cause of most other anti-patterns. They make the code impossible to test in isolation, impossible to reuse, and brittle to change because everything is coupled together.

**Recommendation:** Split the file by responsibility. Each file should answer one question: "What does this do?" — and the answer should fit in one sentence. Use the MVC layers defined in `04-mvc-architecture.md` as the splitting guide.

---

### P05 — Business Logic in Routes/Controllers

**Severity:** HIGH

**Detection signals:**
- Route handler functions that contain: conditional branching on business rules, calculations, discount/tax logic, status transition rules, or notification triggers
- Database queries embedded directly inside route handler functions (not delegated to a model layer)
- Validation logic that goes beyond "is this field present?" (e.g., category membership checks, business invariants)
- `print("SENDING EMAIL: ...")` or `print("SENDING SMS: ...")` inside route handlers — placeholder business logic

**Examples of positive signals:**
```python
# Route handler doing business logic — BAD
def criar_pedido():
    total = 0
    for item in itens:
        # inventory check, price calculation — this is business logic
        if produto["estoque"] < item["quantidade"]:
            return jsonify({"erro": "Estoque insuficiente"}), 400
        total += produto["preco"] * item["quantidade"]
```

**Impact:** Business logic in routes cannot be unit-tested without spinning up an HTTP server. It cannot be reused by other entry points (CLI, workers, other endpoints). Changes to business rules require touching HTTP-layer code.

**Recommendation:** Extract business logic into a dedicated controller or service layer. The route handler should only: parse the HTTP request, call a controller function, and return the response.

---

### P06 — Missing Authentication / Authorization

**Severity:** HIGH

**Detection signals:**
- Endpoints that return user data, modify records, or perform administrative actions without checking a session token, JWT, or session cookie
- Admin endpoints (`/admin/*`, `/reset-db`, `/query`, `/debug`) accessible without any auth check
- No auth middleware registered on protected route groups
- `listar_todos_pedidos()` or similar admin-level operations with no `@login_required` or token verification
- Endpoints that accept `usuario_id` as a body parameter without verifying the caller owns that ID

**High-priority signals (report even if uncertain):**
- Any `DELETE`, `PUT`, or `POST` endpoint with no visible auth check
- Any endpoint with "admin" in its path that has no auth guard
- Endpoints that return data for a specific user ID passed by the client

**Impact:** Unauthenticated users can read all data, impersonate other users, or destroy data. Admin endpoints without auth are a complete system takeover risk.

**Recommendation:** Implement an authentication middleware (JWT verification or session check) and apply it to all non-public endpoints. Use authorization checks to ensure users can only access their own resources.

---

### P07 — Sensitive Data Exposure

**Severity:** HIGH

**Detection signals:**
- API responses that include `senha` / `password` / `passwd` fields
- API responses that include `secret_key`, `api_key`, `token`, `private_key`, or `auth_token` fields
- `/health` or `/status` endpoints that return internal configuration: `secret_key`, `db_path`, `debug` mode flag, server internals
- `SELECT *` queries whose results are serialized and returned directly without field filtering
- User objects returned from login endpoints that include the password hash

**Examples of positive signals:**
```python
# Returning password hash in API response — BAD
return jsonify({"id": row["id"], "nome": row["nome"], "email": row["email"], "senha": row["senha"]})

# Health endpoint leaking config — BAD
return jsonify({"secret_key": "minha-chave-super-secreta-123", "db_path": "loja.db"})
```

**Impact:** Leaked password hashes can be cracked offline. Leaked secret keys allow JWT forgery or session hijacking. Leaked infrastructure details help attackers map the system.

**Recommendation:** Explicitly whitelist the fields returned in every API response. Never return password fields. Remove infrastructure details from health check responses.

---

## MEDIUM Patterns

---

### P08 — N+1 Queries

**Severity:** MEDIUM

**Detection signals:**
- A loop that executes a database query on each iteration: `for item in items: cursor.execute("SELECT ... WHERE id = " + str(item["id"]))`
- Nested cursors or nested DB calls inside a result-iteration loop
- A function that fetches a list of records, then fetches related records one-by-one for each

**Classic N+1 pattern:**
```python
orders = get_all_orders()       # 1 query
for order in orders:
    items = get_items(order.id) # N queries — one per order
```

**Impact:** For N records, this executes N+1 queries. With 1,000 orders, a single endpoint makes 1,001 database round-trips. This causes severe performance degradation at scale.

**Recommendation:** Use a JOIN query to fetch related data in a single query, or use batch fetching (fetch all IDs, then `WHERE id IN (...)`). With an ORM, use eager loading / `joinedload`.

---

### P09 — Code Duplication

**Severity:** MEDIUM

**Detection signals:**
- The same validation logic (required field checks, range checks) copy-pasted across multiple route handlers
- Identical or near-identical error response patterns repeated in every function
- The same database connection setup pattern repeated in every model function
- Functions with different names but identical bodies differing only in table/variable names

**Measuring signals:**
- 5+ lines of identical code appearing in 3+ locations
- The same `if not dados` / `return jsonify({"erro": ...})` block copy-pasted everywhere

**Impact:** Duplicated code means bugs must be fixed in multiple places. Changes to validation rules require hunting through every copy. Missed copies create silent inconsistencies.

**Recommendation:** Extract repeated logic into shared utility functions or base classes. Validation logic belongs in the controller layer as a shared validator. Error responses should come from a centralized error handler.

---

### P10 — Deprecated APIs

**Severity:** MEDIUM

**Detection signals:**
- Use of Python 2-style string formatting (`%s` formatting for display strings, not DB)
- `distutils` imports (removed in Python 3.12)
- `flask.ext.*` imports (removed in Flask 1.0)
- `collections.Callable` instead of `collections.abc.Callable`
- Node.js: `require('url').parse()` instead of `new URL()`
- Node.js: `Buffer()` constructor instead of `Buffer.from()`
- Any import that produces a `DeprecationWarning` at runtime
- Framework-specific patterns the installed version has deprecated (check changelog)

**Impact:** Deprecated APIs may be removed in future versions, causing silent failures or hard crashes on upgrades. They often carry known security or behavioral bugs that were fixed in the replacement API.

**Recommendation:** Replace deprecated calls with their modern equivalents. Check the framework/runtime changelog for the specific migration path.

---

### P11 — Bare Except / Silent Errors

**Severity:** MEDIUM

**Detection signals:**
- `except:` with no exception type specified (Python)
- `except Exception as e:` where `e` is never logged, only `pass` or an empty response returned
- `try { ... } catch (e) {}` with empty catch body (JavaScript)
- `try { ... } catch (e) { console.log(e) }` where the error is swallowed without re-raising or returning an error response
- Error handlers that return HTTP 200 on exceptions

**Examples of positive signals:**
```python
except Exception as e:
    pass  # swallowed — BAD

except:  # catches KeyboardInterrupt, SystemExit — BAD
    return jsonify({"erro": "algo deu errado"}), 500
```

**Impact:** Silent errors hide bugs entirely. A bare `except` also catches `KeyboardInterrupt` and `SystemExit`, preventing clean shutdowns. Without specific exception types, the code handles legitimate errors and programming bugs identically.

**Recommendation:** Catch specific exception types. Always log the exception with stack trace using a proper logger (not `print`). Re-raise or return an appropriate error response. Use a centralized error handler to avoid repeating this logic.

---

## LOW Patterns

---

### P12 — Print Statements as Logging

**Severity:** LOW

**Detection signals:**
- `print(...)` used to report application events, errors, or debug info in production code
- `console.log(...)` in Node.js production route handlers or business logic
- Print statements that contain structured data meant for monitoring: `print("ERRO: " + str(e))`, `print("Usuário criado: " + email)`

**What is NOT a signal:**
- `print()` in a CLI script or a migration tool that is intended to produce terminal output
- `print()` in test files

**Impact:** Print statements go to stdout with no structure, no severity level, no timestamps, and no way to route them to log aggregators. They cannot be silenced in production without code changes. They make debugging and monitoring impossible at scale.

**Recommendation:** Replace `print` with a structured logger: `import logging` in Python, or `winston`/`pino` in Node.js. Configure log levels so debug-level messages are suppressed in production.

---

### P13 — Dead Code

**Severity:** LOW

**Detection signals:**
- Functions defined but never called anywhere in the codebase
- Imports that are never used in the file
- Variables assigned but never read
- Commented-out code blocks that have been left in for extended periods
- Entire files that are never imported or required
- Endpoints registered but never documented and returning only placeholder responses

**Measuring signals:**
- Search for function names — if a function name only appears in its own definition and nowhere else, it is likely dead
- `import X` at the top of a file, but `X` never referenced in the file body

**Impact:** Dead code adds cognitive load without contributing functionality. It misleads future developers into thinking code is in use. It can contain outdated security patterns or bugs that survive because no one thinks to remove them.

**Recommendation:** Remove dead code. Version control preserves history if you ever need to recover it. For functions that might be needed in the future, add a comment explaining why they are kept.

---

### P14 — Magic Numbers / Magic Strings

**Severity:** LOW

**Detection signals:**
- Numeric literals used in logic without explanation: `if faturamento > 10000`, `if len(nome) > 200`, `if len(nome) < 2`
- String literals used as status codes or category names in multiple places: `"pendente"`, `"aprovado"`, `"informatica"`
- HTTP status codes used as raw numbers in multiple places without a constant
- Thresholds, limits, and timeouts as bare numbers with no named constant

**Examples of positive signals:**
```python
if faturamento > 10000:      # What is 10000? Why this threshold?
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```

**Impact:** Magic values are impossible to change consistently — you have to find every occurrence. Their meaning is opaque to readers. When the business rule changes (e.g., the discount threshold moves from 10000 to 15000), developers may miss some occurrences.

**Recommendation:** Define named constants at the module level or in a config file. Use enums for finite sets of values (order statuses, categories). Give every threshold and limit a name that explains its business meaning.
