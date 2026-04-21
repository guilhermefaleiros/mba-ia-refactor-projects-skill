# Security & Quality Audit Report

## Project Metadata

| Field         | Value                                    |
| ------------- | ---------------------------------------- |
| Project       | code-smells-project                      |
| Language      | Python 3                                 |
| Framework     | Flask 3.1.1                              |
| Database      | SQLite via sqlite3 (raw queries, no ORM) |
| Files scanned | 4                                        |
| LOC           | ~784                                     |
| Scan date     | 2026-04-21                               |

---

## Executive Summary

| Severity  | Count  |
| --------- | ------ |
| CRITICAL  | 8      |
| HIGH      | 7      |
| MEDIUM    | 4      |
| LOW       | 4      |
| **TOTAL** | **23** |

This codebase has pervasive SQL injection vulnerabilities across every model function, a fully unauthenticated `/admin/query` endpoint that executes arbitrary attacker-supplied SQL, and passwords stored in plaintext with no hashing whatsoever. All CRITICAL findings must be resolved before this application can be safely deployed in any environment.

---

## Findings

### CRITICAL

---

#### [C1] SQL Injection — Product Model Queries

| Field    | Value                                  |
| -------- | -------------------------------------- |
| Severity | CRITICAL                               |
| Pattern  | P01 — SQL Injection                    |
| Location | `models.py` lines 28, 48–50, 57–63, 68 |

**Description:**
Four product model functions build SQL strings via concatenation. Examples: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (line 28); `"INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "', ..."` (lines 48–50); `"UPDATE produtos SET nome = '" + nome + "', ..."` (lines 57–63); `"DELETE FROM produtos WHERE id = " + str(id)` (line 68). All four pass user-controlled values directly into query strings.

**Impact:**
An attacker can manipulate the SQL query to dump the entire database, modify or delete records, or execute administrative operations. This is the most exploited class of web vulnerability.

**Recommendation:**
Replace all string-concatenated queries with parameterized queries using `?` placeholders: `cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`.

---

#### [C2] SQL Injection — User Authentication Query (Auth Bypass)

| Field    | Value                     |
| -------- | ------------------------- |
| Severity | CRITICAL                  |
| Pattern  | P01 — SQL Injection       |
| Location | `models.py` lines 109–111 |

**Description:**
The login query is built via string concatenation: `cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")`. Submitting `email = "' OR '1'='1' --"` bypasses authentication entirely and logs in as the first user in the database.

**Impact:**
An attacker can authenticate as any user — including admin — without knowing a valid password. This is a complete authentication bypass.

**Recommendation:**
Use a parameterized query: `cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))`, then verify the password separately with a timing-safe comparison after fetching the record.

---

#### [C3] SQL Injection — User Registration and Lookup Queries

| Field    | Value                         |
| -------- | ----------------------------- |
| Severity | CRITICAL                      |
| Pattern  | P01 — SQL Injection           |
| Location | `models.py` lines 92, 126–129 |

**Description:**
`get_usuario_por_id` uses `"SELECT * FROM usuarios WHERE id = " + str(id)` (line 92). `criar_usuario` concatenates `nome`, `email`, `senha`, and `tipo` directly into an INSERT string (lines 126–129), allowing second-order SQL injection via registration.

**Impact:**
Malicious values in registration fields persist in the database and can trigger injection at query time, enabling data exfiltration or privilege escalation on subsequent reads.

**Recommendation:**
Parameterize all queries: `cursor.execute("INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)", (nome, email, hashed_password, tipo))`.

---

#### [C4] SQL Injection — Order Model Queries

| Field    | Value                                                     |
| -------- | --------------------------------------------------------- |
| Severity | CRITICAL                                                  |
| Pattern  | P01 — SQL Injection                                       |
| Location | `models.py` lines 140–166, 174, 188–193, 220–225, 280–282 |

**Description:**
Every order-related query uses string concatenation. Examples: the `criar_pedido` loop at lines 140 and 155 queries products by `item["produto_id"]` using `+ str(...)`. The INSERT at line 148 embeds `usuario_id` and `total` directly. `atualizar_status_pedido` at line 280 concatenates `novo_status` into an UPDATE string. Nested cursor loops at lines 188–193 and 220–225 re-execute per-row queries via concatenation.

**Impact:**
Covers the full order lifecycle: order creation, item insertion, status updates, and order fetching — all injectable by a malicious client body or URL parameter.

**Recommendation:**
Parameterize all queries. For the nested cursor loop pattern, collect product IDs and use `WHERE id IN (?, ?, ?)` in a single query to also address the N+1 issue.

---

#### [C5] SQL Injection — Dynamic Product Search Query Builder

| Field    | Value                     |
| -------- | ------------------------- |
| Severity | CRITICAL                  |
| Pattern  | P01 — SQL Injection       |
| Location | `models.py` lines 289–296 |

**Description:**
`buscar_produtos` builds a dynamic SQL string by appending user-supplied `termo`, `categoria`, `preco_min`, and `preco_max` directly: `query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"`. A search term of `%' UNION SELECT nome, senha, tipo, id, email, criado_em FROM usuarios --` would exfiltrate the users table.

**Impact:**
Search functionality is a common attack vector because it is publicly accessible. Union-based injection here can return data from any table in the database.

**Recommendation:**
Use parameterized LIKE expressions: `query += " AND (nome LIKE ? OR descricao LIKE ?)"` and pass `(f"%{termo}%", f"%{termo}%")` as bound parameters.

---

#### [C6] SQL Injection — Arbitrary SQL Execution Endpoint

| Field    | Value                |
| -------- | -------------------- |
| Severity | CRITICAL             |
| Pattern  | P01 — SQL Injection  |
| Location | `app.py` lines 59–78 |

**Description:**
The `/admin/query` POST endpoint reads a `sql` field from the request body and executes it verbatim: `cursor.execute(query)`. Any client can send `{"sql": "DROP TABLE usuarios"}` or `{"sql": "SELECT * FROM usuarios"}` with no authentication check whatsoever.

**Impact:**
This endpoint is a complete database takeover vector. Any unauthenticated HTTP client can read all data, delete all tables, or insert backdoor admin accounts.

**Recommendation:**
Remove this endpoint entirely — there is no safe way to expose a raw SQL execution API. If database introspection tooling is needed, use a protected admin interface with strong authentication, not an HTTP endpoint.

---

#### [C7] Hardcoded Secret Key

| Field    | Value                       |
| -------- | --------------------------- |
| Severity | CRITICAL                    |
| Pattern  | P02 — Hardcoded Credentials |
| Location | `app.py` line 7             |

**Description:**
`app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` is committed in source. This key signs Flask session cookies; knowing it allows an attacker to forge sessions for any user including admin.

**Impact:**
Credentials committed to source control are permanently exposed in git history. Anyone with read access can authenticate as any user by forging a signed session cookie.

**Recommendation:**
Move to an environment variable: `app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]`. Generate a cryptographically random key (`python -c "import secrets; print(secrets.token_hex(32))"`) and store it in `.env` (gitignored). Document it in `.env.example`.

---

#### [C8] Plaintext Password Storage (No Hashing)

| Field    | Value                                                |
| -------- | ---------------------------------------------------- |
| Severity | CRITICAL                                             |
| Pattern  | P03 — Insecure Hashing                               |
| Location | `models.py` lines 105–131, `database.py` lines 75–83 |

**Description:**
Passwords are stored in the `usuarios` table as plain strings. `criar_usuario` inserts `senha` directly (line 127). `login_usuario` compares passwords with a SQL equality check (line 110). Seed data at `database.py` lines 75–78 hardcodes plaintext passwords `"admin123"`, `"123456"`, `"senha123"` in source.

**Impact:**
Any database read — via SQL injection, a backup leak, or direct file access to `loja.db` — immediately exposes every user's raw password. No cracking needed.

**Recommendation:**
Hash passwords with `bcrypt` (`pip install bcrypt`) before storing: `bcrypt.hashpw(senha.encode(), bcrypt.gensalt())`. At login, fetch the user by email and verify with `bcrypt.checkpw(senha.encode(), stored_hash)`. Remove hardcoded seed passwords from source.

---

### HIGH

---

#### [H1] God File — models.py Mixes Data Access and Business Logic

| Field    | Value                      |
| -------- | -------------------------- |
| Severity | HIGH                       |
| Pattern  | P04 — God Class / God File |
| Location | `models.py` lines 1–315    |

**Description:**
`models.py` is 315 lines and handles four distinct responsibilities: raw SQL for products, raw SQL for users, raw SQL for orders, and embedded business logic including inventory management (`criar_pedido` lines 133–169) and discount tier calculation (`relatorio_vendas` lines 256–268).

**Impact:**
Business rules are impossible to unit-test without a live database. Discount logic and inventory management are buried inside data-access functions, making them invisible to the service layer and unresolvable without changing the model layer.

**Recommendation:**
Split into separate modules: `models/produto.py`, `models/usuario.py`, `models/pedido.py` — each handling only SQL for its entity. Extract discount calculation and inventory orchestration into a `services/pedido_service.py`.

---

#### [H2] Business Logic in Controller Layer — Order Processing

| Field    | Value                                      |
| -------- | ------------------------------------------ |
| Severity | HIGH                                       |
| Pattern  | P05 — Business Logic in Routes/Controllers |
| Location | `controllers.py` lines 208–210, 247–251    |

**Description:**
`criar_pedido` contains notification stubs at lines 208–210 (`print("ENVIANDO EMAIL: ...")`, `print("ENVIANDO SMS: ...")`, `print("ENVIANDO PUSH: ...")`). `atualizar_status_pedido` at lines 247–251 applies business status-transition rules and triggers conditional notifications inline.

**Impact:**
Notification and status-transition rules cannot be unit-tested without an HTTP call, and cannot be reused by CLI scripts or async workers. Changing the notification strategy requires touching the HTTP controller.

**Recommendation:**
Extract to `services/notificacao_service.py` and `services/pedido_service.py`. The controller calls `pedido_service.processar_pedido(dados)` and delegates all domain logic downstream.

---

#### [H3] Business Logic in Data Layer — Discount Calculation and Inventory

| Field    | Value                                      |
| -------- | ------------------------------------------ |
| Severity | HIGH                                       |
| Pattern  | P05 — Business Logic in Routes/Controllers |
| Location | `models.py` lines 133–169, 256–268         |

**Description:**
`criar_pedido` (lines 133–169) performs inventory validation, price multiplication, and stock decrement inside what should be a pure data-access function. `relatorio_vendas` (lines 256–268) applies tiered discount calculation logic (`if faturamento > 10000: desconto = faturamento * 0.1`) in the model layer.

**Impact:**
Business rules embedded in the data layer cannot be tested in isolation, cannot be changed without risk of breaking queries, and are invisible to the controller layer that should own orchestration.

**Recommendation:**
Move discount logic and inventory management to `services/pedido_service.py`. `models/pedido.py` should only contain SQL insert/select/update functions; the service layer orchestrates the transaction.

---

#### [H4] Missing Authentication — Admin Endpoints Fully Unprotected

| Field    | Value                                        |
| -------- | -------------------------------------------- |
| Severity | HIGH                                         |
| Pattern  | P06 — Missing Authentication / Authorization |
| Location | `app.py` lines 47–78                         |

**Description:**
Both `/admin/reset-db` (lines 47–57) and `/admin/query` (lines 59–78) have no authentication check of any kind. Any HTTP client can DELETE all rows from all tables or execute arbitrary SQL with zero credentials.

**Impact:**
Unauthenticated admin endpoints are a complete system takeover risk. A single POST request from anywhere on the network destroys all data or exfiltrates the entire database.

**Recommendation:**
`/admin/query` should be removed entirely (see C6). `/admin/reset-db` should be removed or protected behind a strong auth middleware limited to a trusted IP range and an admin JWT.

---

#### [H5] Missing Authorization — User and Order Listing Endpoints

| Field    | Value                                        |
| -------- | -------------------------------------------- |
| Severity | HIGH                                         |
| Pattern  | P06 — Missing Authentication / Authorization |
| Location | `controllers.py` lines 128–134, 222–235      |

**Description:**
`listar_usuarios` (lines 128–134) returns all user records including password hashes to any caller. `listar_todos_pedidos` (lines 229–235) returns every order from every user. `listar_pedidos_usuario` (lines 222–227) accepts a `usuario_id` URL parameter with no check that the caller owns that ID — any authenticated user can read any other user's orders.

**Impact:**
Any unauthenticated client can enumerate all users and all orders. A logged-in user can access other users' order history by changing the `usuario_id` in the URL.

**Recommendation:**
Add an authentication middleware that validates a JWT or session token on every protected route. Add an ownership check in `listar_pedidos_usuario` to verify the token's `sub` matches `usuario_id`.

---

#### [H6] Sensitive Data Exposure — Passwords in API Responses

| Field    | Value                           |
| -------- | ------------------------------- |
| Severity | HIGH                            |
| Pattern  | P07 — Sensitive Data Exposure   |
| Location | `models.py` lines 79–87, 93–102 |

**Description:**
Both `get_todos_usuarios` (lines 79–87) and `get_usuario_por_id` (lines 93–102) include `"senha": row["senha"]` in the returned dict, which flows directly into the JSON response payload of `listar_usuarios` and `buscar_usuario`.

**Impact:**
Every `/usuarios` GET request currently returns plaintext passwords (or hashes, once C8 is fixed) to any caller. This negates any password protection — attackers can simply GET the list.

**Recommendation:**
Remove `"senha"` from all response dicts. Explicitly whitelist only `id`, `nome`, `email`, `tipo`, `criado_em`.

---

#### [H7] Sensitive Data Exposure — Secret Key and Config in Health Check

| Field    | Value                          |
| -------- | ------------------------------ |
| Severity | HIGH                           |
| Pattern  | P07 — Sensitive Data Exposure  |
| Location | `controllers.py` lines 285–291 |

**Description:**
The `/health` response at lines 285–291 explicitly returns `"secret_key": "minha-chave-super-secreta-123"`, `"db_path": "loja.db"`, `"debug": True`, and `"ambiente": "producao"`. This leaks the session signing key and internal infrastructure details in a public endpoint.

**Impact:**
Leaked secret keys allow JWT forgery or session hijacking. Leaked infrastructure details (DB path, debug mode, environment name) assist attackers in targeting follow-up attacks.

**Recommendation:**
Reduce the health check to operational signals only: `{"status": "ok", "database": "connected", "counts": {...}}`. Remove all configuration values.

---

### MEDIUM

---

#### [M1] N+1 Queries — get_pedidos_usuario

| Field    | Value                     |
| -------- | ------------------------- |
| Severity | MEDIUM                    |
| Pattern  | P08 — N+1 Queries         |
| Location | `models.py` lines 171–201 |

**Description:**
`get_pedidos_usuario` fetches all orders (1 query), then for each order fetches its items (N queries), then for each item fetches the product name (M queries per order). For a user with 10 orders averaging 3 items each, this is 1 + 10 + 30 = 41 database round-trips.

**Impact:**
At scale (hundreds of orders), a single `/pedidos/usuario/<id>` request triggers hundreds of queries, causing severe response latency and database contention.

**Recommendation:**
Replace the nested loop with a single JOIN query: `SELECT p.*, ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome as produto_nome FROM pedidos p JOIN itens_pedido ip ON ip.pedido_id = p.id JOIN produtos pr ON pr.id = ip.produto_id WHERE p.usuario_id = ?` and aggregate in Python.

---

#### [M2] N+1 Queries — get_todos_pedidos

| Field    | Value                     |
| -------- | ------------------------- |
| Severity | MEDIUM                    |
| Pattern  | P08 — N+1 Queries         |
| Location | `models.py` lines 203–233 |

**Description:**
`get_todos_pedidos` has the identical nested cursor pattern as `get_pedidos_usuario` but applied to the entire orders table. For 100 orders with 3 items each, this is 401 queries per request to `/pedidos`.

**Impact:**
This endpoint is the most destructive for performance because it has no user filter — it fetches all orders. A single admin page load could execute thousands of queries.

**Recommendation:**
Same JOIN approach as M1. This function and `get_pedidos_usuario` share identical logic and should be unified into one parameterized query function.

---

#### [M3] Code Duplication — Product Validation Logic

| Field    | Value                               |
| -------- | ----------------------------------- |
| Severity | MEDIUM                              |
| Pattern  | P09 — Code Duplication              |
| Location | `controllers.py` lines 28–50, 72–93 |

**Description:**
`criar_produto` and `atualizar_produto` contain near-identical validation blocks: both check that `dados` is present, that `nome`/`preco`/`estoque` fields exist, that `preco` and `estoque` are non-negative, and parse the same fields into local variables. The validation logic spans ~20 lines in each function and differs only in that `atualizar_produto` first checks if the product exists.

**Impact:**
Any change to product validation rules (e.g., adding a minimum price) requires updating two places. Missed updates create silent inconsistencies between create and update behavior.

**Recommendation:**
Extract a shared `validar_dados_produto(dados)` function in the controller layer that returns either validated values or a validation error. Both handlers call it before proceeding.

---

#### [M4] Generic Exception Handling Leaks Internal Error Details

| Field    | Value                                                                              |
| -------- | ---------------------------------------------------------------------------------- |
| Severity | MEDIUM                                                                             |
| Pattern  | P11 — Bare Except / Silent Errors                                                  |
| Location | `controllers.py` lines 12, 22, 60, 95, 126, 144, 165, 186, 220, 227, 255, 262, 292 |

**Description:**
Every controller function catches `except Exception as e:` and returns `jsonify({"erro": str(e)})` to the caller. This means raw Python exception messages — including SQLite error text that may contain table names, column names, or partial query content — are sent to the client.

**Impact:**
Exception messages provide attackers with precise information about internal structure: table names, column names, query format, Python types. This directly aids SQL injection reconnaissance.

**Recommendation:**
Log the full exception server-side with a structured logger (`logging.exception(...)`). Return a generic error message to clients: `{"erro": "Erro interno do servidor"}`. Use a centralized Flask error handler registered with `@app.errorhandler(Exception)`.

---

### LOW

---

#### [L1] Print Statements Used for Application Logging

| Field    | Value                                                                                                  |
| -------- | ------------------------------------------------------------------------------------------------------ |
| Severity | LOW                                                                                                    |
| Pattern  | P12 — Print Statements as Logging                                                                      |
| Location | `controllers.py` lines 8, 11, 57, 107, 161, 179, 182, 208–210, 219, 248, 250; `app.py` lines 56, 83–86 |

**Description:**
All application events — user creation, login attempts, order creation, errors, and admin resets — are reported via `print(...)`. Examples: `print("Usuário criado: " + email)`, `print("ENVIANDO EMAIL: ...")`, `print("!!! BANCO DE DADOS RESETADO !!!")`.

**Impact:**
Print output has no severity level, no timestamps, and no way to route to log aggregators. Debug noise cannot be suppressed in production without code changes.

**Recommendation:**
Replace all `print` calls with `import logging; logger = logging.getLogger(__name__)` and use `logger.info(...)`, `logger.error(...)`, etc. Configure log level via environment variable.

---

#### [L2] Unused Import — `os` in database.py

| Field    | Value                |
| -------- | -------------------- |
| Severity | LOW                  |
| Pattern  | P13 — Dead Code      |
| Location | `database.py` line 2 |

**Description:**
`import os` is declared at line 2 of `database.py` but `os` is never referenced anywhere in the file.

**Impact:**
Adds cognitive load; readers may expect `os` to be used (e.g., for path resolution) and search for it.

**Recommendation:**
Remove the unused import.

---

#### [L3] Magic Numbers in Discount Calculation

| Field    | Value                               |
| -------- | ----------------------------------- |
| Severity | LOW                                 |
| Pattern  | P14 — Magic Numbers / Magic Strings |
| Location | `models.py` lines 256–268           |

**Description:**
`relatorio_vendas` uses bare numeric literals for business thresholds and rates: `faturamento > 10000`, `faturamento > 5000`, `faturamento > 1000`, `faturamento * 0.1`, `faturamento * 0.05`, `faturamento * 0.02`. None are named or explained.

**Impact:**
When the discount tiers change (e.g., threshold moved from 10000 to 15000), developers must find every occurrence. The business meaning of each number is opaque to readers.

**Recommendation:**
Define named constants: `DESCONTO_TIER_ALTO = 10000`, `TAXA_DESCONTO_ALTO = 0.10`, etc., or extract into a configuration structure. Consider using an enum or dataclass for the discount tiers.

---

#### [L4] Magic Strings for Order Statuses and Product Categories

| Field    | Value                               |
| -------- | ----------------------------------- |
| Severity | LOW                                 |
| Pattern  | P14 — Magic Numbers / Magic Strings |
| Location | `controllers.py` lines 52, 242      |

**Description:**
Product categories are defined as an inline list literal at line 52: `["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]`. Order statuses are an inline list at line 242: `["pendente", "aprovado", "enviado", "entregue", "cancelado"]`. These same string values are also used in `database.py` seed data and scattered throughout `models.py`.

**Impact:**
Adding a new status or category requires finding all occurrences across files. A typo in any one occurrence creates a silent mismatch.

**Recommendation:**
Define `from enum import Enum` classes `CategoriaEnum` and `StatusPedidoEnum` in a shared `config.py` or `constants.py` and import them wherever statuses/categories are referenced.

---

## Footer

**Total findings: 23** (8 critical / 7 high / 4 medium / 4 low)

**Priority action plan:**

1. Fix all CRITICAL findings before deploying to any environment
2. Fix all HIGH findings before accepting user traffic
3. Schedule MEDIUM findings for the next sprint
4. Address LOW findings during regular maintenance
