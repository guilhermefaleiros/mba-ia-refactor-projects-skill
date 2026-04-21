# 05 — Refactoring Playbook

Reference file for Phase 3 of the refactor-arch skill. Each entry shows a problematic pattern (BEFORE) and its corrected form (AFTER). Examples use Python and JavaScript pseudocode. Adapt to the actual language detected in Phase 1.

Apply transformations in severity order: CRITICAL first, then HIGH, then MEDIUM/LOW.

---

## Table of Contents

1. [SQL Injection → Parameterized Queries](#1-sql-injection--parameterized-queries) — CRITICAL
2. [Hardcoded Credentials → Environment Variables](#2-hardcoded-credentials--environment-variables) — CRITICAL
3. [Insecure Hashing → Secure Hashing](#3-insecure-hashing--secure-hashing) — CRITICAL
4. [God Class → Separated Modules](#4-god-class--separated-modules) — HIGH
5. [Business Logic in Routes → Controller Layer](#5-business-logic-in-routes--controller-layer) — HIGH
6. [N+1 Queries → JOINs / Eager Loading](#6-n1-queries--joins--eager-loading) — MEDIUM
7. [Callback Hell → Async/Await](#7-callback-hell--asyncawait) — MEDIUM
8. [Global State → Dependency Injection](#8-global-state--dependency-injection) — MEDIUM
9. [Print → Logging](#9-print--logging) — LOW
10. [Bare Except → Specific Exception Handling](#10-bare-except--specific-exception-handling) — MEDIUM
11. [Sensitive Data Exposure → Response Filtering](#11-sensitive-data-exposure--response-filtering) — HIGH
12. [Dead Code → Cleanup](#12-dead-code--cleanup) — LOW

---

## 1. SQL Injection → Parameterized Queries

**Audit pattern**: P01 — SQL Injection

**Problem**: User-controlled values are concatenated into SQL strings. Any string a user provides becomes executable SQL.

**BEFORE**:
```python
# Python — string concatenation
cursor.execute("SELECT * FROM users WHERE id = " + str(id))
cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
cursor.execute(
    "INSERT INTO products (name, price) VALUES ('" + name + "', " + str(price) + ")"
)

# Python — f-string
cursor.execute(f"SELECT * FROM users WHERE name = '{name}' AND active = 1")

# Dynamic query building via concatenation
query = "SELECT * FROM products WHERE 1=1"
if term:
    query += " AND name LIKE '%" + term + "%'"
cursor.execute(query)
```

**AFTER**:
```python
# Python — SQLite uses ? placeholders
cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
cursor.execute(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    (name, price)
)

# Dynamic query building — collect params alongside placeholders
conditions = []
params = []
if term:
    conditions.append("name LIKE ?")
    params.append(f"%{term}%")

where_clause = " AND ".join(conditions)
query = f"SELECT * FROM products WHERE 1=1"
if conditions:
    query += " AND " + where_clause
cursor.execute(query, params)

# JavaScript — node-postgres uses $1, $2 placeholders
await client.query("SELECT * FROM users WHERE id = $1", [id])
await client.query(
    "INSERT INTO products (name, price) VALUES ($1, $2)",
    [name, price]
)

# JavaScript — mysql2 uses ? placeholders
await connection.execute("SELECT * FROM users WHERE id = ?", [id])
```

**Key rule**: User data goes in the second argument (the params tuple/array). Never inside the query string itself.

---

## 2. Hardcoded Credentials → Environment Variables

**Audit pattern**: P02 — Hardcoded Credentials

**Problem**: Secrets are embedded in source code and committed to version control. They cannot be rotated without changing the code.

**BEFORE**:
```python
# Python — credentials in config
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
DB_PASSWORD = "admin123"
API_KEY = "sk-prod-abc123xyz"
DATABASE_URL = "postgresql://admin:admin123@localhost/mydb"

# JavaScript — credentials in module
const config = {
  secretKey: "hardcoded-jwt-secret",
  dbPassword: "supersecret",
  apiKey: "sk-live-abc123"
}
```

**AFTER**:
```python
# Python — config.py reads from environment
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    API_KEY = os.environ.get("API_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "app.db")  # default OK for non-secrets

    @classmethod
    def validate(cls):
        required = ["SECRET_KEY"]
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {missing}")

# JavaScript — config.js reads from environment
module.exports = {
  secretKey: process.env.SECRET_KEY,
  dbPassword: process.env.DB_PASSWORD,
  apiKey: process.env.API_KEY,
  databaseUrl: process.env.DATABASE_URL || 'app.db',

  validate() {
    const required = ['SECRET_KEY'];
    const missing = required.filter(k => !process.env[k]);
    if (missing.length > 0) {
      throw new Error(`Missing required env vars: ${missing.join(', ')}`);
    }
  }
};
```

**.env.example** (committed to version control, no real values):
```
# Required — the application will not start without these
SECRET_KEY=

# Optional — defaults shown
DATABASE_URL=app.db
DEBUG=false
PORT=5000
```

**.gitignore** (ensure these are ignored):
```
.env
*.env.local
```

**Key rule**: `os.environ.get("KEY")` with no default for secrets. The application must fail at startup if a required secret is absent, not at request time.

---

## 3. Insecure Hashing → Secure Hashing

**Audit pattern**: P03 — Insecure Hashing

**Problem**: MD5, SHA1, and plain SHA256 are too fast for password hashing — they allow billions of guesses per second. Passwords stored this way are recoverable from any stolen database.

**BEFORE**:
```python
# Python — MD5 / SHA1 for passwords
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()
hashed = hashlib.sha1(password.encode()).hexdigest()

# Storing and comparing
user["senha"] = hashlib.md5(senha.encode()).hexdigest()
if user["senha"] == hashlib.md5(input_senha.encode()).hexdigest():
    # authenticated

# JavaScript — crypto module
const crypto = require('crypto');
const hash = crypto.createHash('md5').update(password).digest('hex');
```

**AFTER**:
```python
# Python — bcrypt (pip install bcrypt)
import bcrypt

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Python — argon2 (pip install argon2-cffi)
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(plain_password: str) -> str:
    return ph.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except Exception:
        return False

# JavaScript — bcrypt (npm install bcrypt)
const bcrypt = require('bcrypt');
const ROUNDS = 12;

async function hashPassword(plainPassword) {
  return bcrypt.hash(plainPassword, ROUNDS);
}

async function verifyPassword(plainPassword, hashedPassword) {
  return bcrypt.compare(plainPassword, hashedPassword);
}
```

**Migration note**: Existing passwords hashed with MD5/SHA1 are irrecoverable as bcrypt hashes. The migration path is: on next login, verify against the old hash → re-hash with bcrypt → update the stored hash. This transparently migrates users as they log in. Document this migration process.

---

## 4. God Class → Separated Modules

**Audit pattern**: P04 — God Class / God File

**Problem**: A single file with hundreds of lines handles multiple unrelated responsibilities. Every change to the system touches the same file, causing merge conflicts and making the code unnavigable.

**BEFORE**:
```
controllers.py  (400+ lines)
├── listar_produtos()      — HTTP handler + DB query
├── criar_produto()        — HTTP handler + validation + DB query
├── login()                — HTTP handler + auth logic + DB query
├── criar_pedido()         — HTTP handler + inventory check + total calc + DB query
└── relatorio_vendas()     — HTTP handler + financial calculations + DB query
```

**AFTER**:
```
models/
├── produto.py             — only: get_all, get_by_id, create, update, delete
├── usuario.py             — only: get_all, get_by_id, create, find_by_email
└── pedido.py              — only: create, get_by_user, get_all, update_status

controllers/
├── produto_controller.py  — only: validation rules + orchestration for products
├── usuario_controller.py  — only: login logic, user creation rules
└── pedido_controller.py   — only: order creation rules, stock management, totals

routes/
├── produto_routes.py      — only: HTTP endpoints for /products
├── usuario_routes.py      — only: HTTP endpoints for /users + /login
└── pedido_routes.py       — only: HTTP endpoints for /orders
```

**Splitting heuristic**: Group functions by the question they answer. "Does this deal with the database for products?" → `models/produto`. "Does this know the business rules for creating an order?" → `controllers/pedido_controller`. "Does this parse an HTTP request and return a response?" → `routes/pedido_routes`.

---

## 5. Business Logic in Routes → Controller Layer

**Audit pattern**: P05 — Business Logic in Routes/Controllers

**Problem**: Route handlers contain business rules (inventory checks, discount calculations, state transitions) that cannot be unit-tested without an HTTP server and cannot be reused from other contexts.

**BEFORE**:
```python
# Route handler doing business logic — everything mixed
def criar_pedido():
    dados = request.get_json()
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    total = 0
    for item in itens:
        # Business rule: check stock — belongs in controller
        produto = get_produto(item["produto_id"])
        if produto["estoque"] < item["quantidade"]:
            return jsonify({"erro": "Estoque insuficiente"}), 400
        # Business rule: calculate total — belongs in controller
        total += produto["preco"] * item["quantidade"]

    pedido_id = criar_pedido_db(usuario_id, total, itens)
    return jsonify({"pedido_id": pedido_id}), 201
```

**AFTER**:
```python
# routes/pedido_routes.py — only HTTP concerns
def criar_pedido():
    dados = request.get_json()
    if not dados or "usuario_id" not in dados or "itens" not in dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    resultado = pedido_controller.criar_pedido(
        usuario_id=dados["usuario_id"],
        itens=dados["itens"]
    )
    return jsonify({"dados": resultado, "sucesso": True}), 201

# controllers/pedido_controller.py — business rules live here
def criar_pedido(usuario_id, itens):
    if not itens:
        raise ValueError("Pedido deve ter pelo menos 1 item")

    total = 0
    for item in itens:
        produto = produto_model.get_by_id(item["produto_id"])
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]

    pedido_id = pedido_model.create(usuario_id, total, itens)
    return {"pedido_id": pedido_id, "total": total}
```

**The pattern**: Route handler = parse request → call one controller function → return response. Controller = business rules, no HTTP. Model = data access, no business rules.

---

## 6. N+1 Queries → JOINs / Eager Loading

**Audit pattern**: P08 — N+1 Queries

**Problem**: Fetching a list of records and then making one additional query per record results in N+1 database round-trips. With 1,000 orders, a single endpoint makes 1,001 queries.

**BEFORE**:
```python
# Fetch orders (1 query), then for each order fetch its items (N queries)
def get_orders_with_items():
    orders = cursor.execute("SELECT * FROM pedidos").fetchall()
    result = []
    for order in orders:
        # One extra query per order
        items = cursor.execute(
            "SELECT * FROM itens_pedido WHERE pedido_id = " + str(order["id"])
        ).fetchall()
        # And another for each item's product name
        for item in items:
            product = cursor.execute(
                "SELECT nome FROM produtos WHERE id = " + str(item["produto_id"])
            ).fetchone()
            ...
```

**AFTER**:
```python
# Option A: JOIN — fetch everything in one query
def get_orders_with_items():
    rows = cursor.execute("""
        SELECT
            p.id          AS pedido_id,
            p.usuario_id,
            p.status,
            p.total,
            p.criado_em,
            ip.produto_id,
            ip.quantidade,
            ip.preco_unitario,
            pr.nome       AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        ORDER BY p.id
    """).fetchall()

    # Group rows by pedido_id in application code
    orders = {}
    for row in rows:
        pid = row["pedido_id"]
        if pid not in orders:
            orders[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "itens": []
            }
        if row["produto_id"]:
            orders[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"]
            })
    return list(orders.values())

# Option B: Batch fetch — two queries instead of N+1
def get_orders_with_items():
    orders = cursor.execute("SELECT * FROM pedidos").fetchall()
    order_ids = [o["id"] for o in orders]

    if not order_ids:
        return []

    placeholders = ",".join("?" * len(order_ids))
    items = cursor.execute(
        f"SELECT ip.*, pr.nome AS produto_nome FROM itens_pedido ip "
        f"JOIN produtos pr ON pr.id = ip.produto_id "
        f"WHERE ip.pedido_id IN ({placeholders})",
        order_ids
    ).fetchall()

    # Group items by order_id in memory
    items_by_order = {}
    for item in items:
        items_by_order.setdefault(item["pedido_id"], []).append(dict(item))

    return [
        {**dict(o), "itens": items_by_order.get(o["id"], [])}
        for o in orders
    ]
```

**Choose based on**:
- JOIN: best when all records fit in memory and the relationship is 1:few
- Batch fetch: better when the result set could be very large or when you need pagination

---

## 7. Callback Hell → Async/Await

**Audit pattern**: P10 — Deprecated APIs / Callback patterns

**Problem**: Deeply nested callbacks make code flow impossible to follow and error handling fragile.

**BEFORE** (JavaScript):
```javascript
// Nested callbacks — hard to read, hard to handle errors
app.post('/orders', (req, res) => {
  db.query('SELECT * FROM users WHERE id = ?', [req.body.userId], (err, users) => {
    if (err) return res.status(500).json({ erro: err.message });
    db.query('SELECT * FROM products WHERE id = ?', [req.body.productId], (err, products) => {
      if (err) return res.status(500).json({ erro: err.message });
      db.query('INSERT INTO orders ...', [...], (err, result) => {
        if (err) return res.status(500).json({ erro: err.message });
        res.json({ orderId: result.insertId });
      });
    });
  });
});
```

**AFTER** (JavaScript):
```javascript
// Async/await — linear flow, errors propagate to error handler
app.post('/orders', async (req, res, next) => {
  try {
    const resultado = await pedidoController.criarPedido(
      req.body.usuarioId,
      req.body.itens
    );
    res.status(201).json({ dados: resultado, sucesso: true });
  } catch (err) {
    next(err); // propagate to centralized error handler
  }
});

// In the controller (also async)
async function criarPedido(usuarioId, itens) {
  const usuario = await usuarioModel.findById(usuarioId);
  if (!usuario) throw Object.assign(new Error('Usuário não encontrado'), { status: 404 });

  const total = await calcularTotal(itens);
  const pedidoId = await pedidoModel.create(usuarioId, total, itens);
  return { pedidoId, total };
}
```

**For Python**: Python has native async/await support with `asyncio`. If the current codebase uses synchronous Flask/Django, do not switch to async as part of this refactor — that is a larger migration. Instead, focus on the other patterns. Flag async migration as a future improvement.

---

## 8. Global State → Dependency Injection

**Audit pattern**: Related to P04 — God Class (hidden coupling via globals)

**Problem**: Functions access shared mutable state from module-level variables. This makes testing impossible (state from one test leaks into the next) and makes the data flow invisible.

**BEFORE**:
```python
# Module-level global — hidden dependency
_db_connection = None

def get_db():
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect("app.db")
    return _db_connection

def get_user(user_id):
    db = get_db()  # hidden dependency on global state
    ...
```

**AFTER**:
```python
# Dependency injection — the connection is passed explicitly
def get_user(user_id, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# The route/controller provides the connection
def handle_get_user(user_id):
    with get_db_connection() as db:
        user = get_user(user_id, db)
    return user

# For Flask specifically: use application context (g) for per-request connections
# rather than a module-level singleton
```

**Note**: For web frameworks that use a request context (Flask `g`, Django's thread-local, etc.), the framework-provided pattern for per-request resources is acceptable — use it rather than inventing a custom global. The anti-pattern is a module-level singleton that is shared across requests.

---

## 9. Print → Logging

**Audit pattern**: P12 — Print Statements as Logging

**Problem**: `print()` produces unstructured output with no severity, no timestamps, and no routing capability. It cannot be silenced in production or sent to a log aggregator.

**BEFORE**:
```python
print("Listando " + str(len(produtos)) + " produtos")
print("ERRO: " + str(e))
print("Usuário criado: " + email)
print("!!! BANCO DE DADOS RESETADO !!!")
```

**AFTER**:
```python
# At the top of each module
import logging
logger = logging.getLogger(__name__)

# Replace print calls
logger.info("Listing %d products", len(produtos))
logger.error("Error processing request: %s", e, exc_info=True)
logger.info("User created: %s", email)
logger.warning("Database reset executed")

# Configure logging once in app startup (config.py or app.py)
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s"
)
# In production, set level from environment: LOG_LEVEL=WARNING
```

**JavaScript**:
```javascript
// BEFORE
console.log("Produto criado com ID: " + id);
console.log("ERRO: " + err.message);

// AFTER — using a simple pattern that works without extra dependencies
const logger = {
  info:  (...args) => console.log(new Date().toISOString(), 'INFO', ...args),
  warn:  (...args) => console.warn(new Date().toISOString(), 'WARN', ...args),
  error: (...args) => console.error(new Date().toISOString(), 'ERROR', ...args),
};

logger.info('Product created with id:', id);
logger.error('Error processing request:', err.message, err.stack);
// For production, replace with winston or pino for structured JSON logging
```

**Key change**: Use severity levels. `logger.error()` for exceptions, `logger.info()` for notable events, `logger.debug()` for tracing (suppressed in production).

---

## 10. Bare Except → Specific Exception Handling

**Audit pattern**: P11 — Bare Except / Silent Errors

**Problem**: Catching all exceptions with a bare `except:` or `except Exception:` that then swallows the error hides bugs and prevents proper error propagation. A bare `except:` in Python also catches `KeyboardInterrupt` and `SystemExit`.

**BEFORE**:
```python
# Swallows everything including programming errors
try:
    resultado = processar_pedido(dados)
except:
    pass

# Catches and silently returns 500
try:
    usuario = get_usuario(id)
    return jsonify(usuario)
except Exception as e:
    return jsonify({"erro": str(e)}), 500  # e is never logged
```

**AFTER**:
```python
# Catch specific exceptions and handle meaningfully
from sqlite3 import IntegrityError, OperationalError

def get_usuario(id, db):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"User {id} not found")
        return dict(row)
    except OperationalError as e:
        logger.error("Database error fetching user %d: %s", id, e)
        raise  # re-raise; let the centralized error handler respond

# In the route layer — only catch what you can meaningfully handle here
# Everything else propagates to the centralized error handler
def handle_get_user(user_id):
    try:
        user = usuario_controller.get_usuario(user_id)
        return jsonify({"dados": user, "sucesso": True}), 200
    except ValueError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 404
    # All other exceptions propagate up — centralized handler returns 500
```

**JavaScript**:
```javascript
// BEFORE — empty catch
try {
  const result = await processOrder(data);
} catch (e) {}

// AFTER — specific handling and propagation
async function criarPedido(usuarioId, itens) {
  // Validate input — throw with a status code for HTTP handlers to use
  if (!itens || itens.length === 0) {
    const err = new Error('Pedido deve ter ao menos 1 item');
    err.status = 400;
    throw err;
  }
  // Database errors propagate naturally — no swallowing
  const pedidoId = await pedidoModel.create(usuarioId, itens);
  return { pedidoId };
}
```

---

## 11. Sensitive Data Exposure → Response Filtering

**Audit pattern**: P07 — Sensitive Data Exposure

**Problem**: API responses include password hashes, secret keys, or internal infrastructure details that should never leave the server.

**BEFORE**:
```python
# Returning password hash — NEVER acceptable
def get_todos_usuarios():
    rows = cursor.execute("SELECT * FROM usuarios").fetchall()
    return [dict(row) for row in rows]  # includes senha field!

# Health endpoint leaking config
def health_check():
    return jsonify({
        "status": "ok",
        "secret_key": app.config["SECRET_KEY"],  # leaks secret
        "db_path": "loja.db",                     # leaks infrastructure
        "debug": True
    })
```

**AFTER**:
```python
# Explicit field whitelist — only safe fields returned
USUARIO_PUBLIC_FIELDS = {"id", "nome", "email", "tipo", "criado_em"}
PRODUTO_PUBLIC_FIELDS = {"id", "nome", "descricao", "preco", "estoque", "categoria", "criado_em"}

def serialize_usuario(row):
    """Return only safe fields. Never include senha, tokens, or internal ids."""
    data = dict(row) if not isinstance(row, dict) else row
    return {k: v for k, v in data.items() if k in USUARIO_PUBLIC_FIELDS}

def get_todos_usuarios(db):
    rows = db.cursor().execute("SELECT * FROM usuarios").fetchall()
    return [serialize_usuario(row) for row in rows]

# Health endpoint — only operational data, no config
def health_check(db):
    try:
        db.cursor().execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "error", "database": "disconnected"}
```

**JavaScript**:
```javascript
// Explicit safe serialization
const USUARIO_PUBLIC_FIELDS = ['id', 'nome', 'email', 'tipo', 'criadoEm'];

function serializeUsuario(row) {
  return Object.fromEntries(
    Object.entries(row).filter(([k]) => USUARIO_PUBLIC_FIELDS.includes(k))
  );
}
```

**Key rule**: Define a serialization function for each entity that explicitly lists permitted fields. Never return `SELECT *` results directly without filtering.

---

## 12. Dead Code → Cleanup

**Audit pattern**: P13 — Dead Code

**Problem**: Functions, imports, and variables that are defined but never used add confusion, mislead maintainers, and occasionally harbor outdated security patterns.

**BEFORE**:
```python
import os          # imported but never used
import hashlib     # imported but never used after refactor

# Function defined but never called anywhere
def _old_authenticate(username, password):
    return hashlib.md5(password.encode()).hexdigest() == get_stored_hash(username)

# Commented-out code left indefinitely
# def create_session(user_id):
#     session_token = str(uuid.uuid4())
#     sessions[user_id] = session_token
#     return session_token

# Variable assigned but never read
DEPRECATED_API_URL = "https://old-api.example.com/v1"
```

**AFTER**:
```python
# Remove unused imports
# Remove dead functions
# Remove commented-out code blocks
# Remove unused variables

# If you're unsure whether something is actually dead:
# 1. Search the entire codebase for the function/variable name
# 2. Check git log to understand when it was last used and why it was removed
# 3. If it was intentionally kept for future use, add a comment explaining why
#    and when it is expected to be used
```

**Safe removal checklist**:
- [ ] Searched the entire codebase for the name — zero references outside the definition
- [ ] Checked git history — no recent removal of callers that suggests this is temporarily unused
- [ ] No tests reference the dead code (even commented-out tests)
- [ ] No external documentation (README, API docs) refers to this feature

**Note**: Version control preserves history. Deleted code can always be recovered from git. There is no need to comment it out "just in case."
