# 01 — Project Analysis Heuristics

Reference file for Phase 1 of the refactor-arch skill. Apply these heuristics to produce the Phase 1 report.

---

## 1. Language Detection

Look for these signals in priority order (first strong signal wins):

| Signal | Language |
|--------|----------|
| `*.py` files + `requirements.txt` or `pyproject.toml` or `setup.py` | Python |
| `*.js` / `*.ts` files + `package.json` | JavaScript / TypeScript |
| `*.java` files + `pom.xml` or `build.gradle` | Java |
| `*.go` files + `go.mod` | Go |
| `*.rb` files + `Gemfile` | Ruby |
| `*.php` files + `composer.json` | PHP |
| `*.cs` files + `*.csproj` or `*.sln` | C# |
| `*.rs` files + `Cargo.toml` | Rust |
| Shebang `#!/usr/bin/env python` or `#!/usr/bin/env node` at top of entry file | Python / Node |

If multiple languages are present, identify the **primary** language (the one the entry point uses) and note secondary languages (e.g., "Python with shell scripts").

---

## 2. Framework Detection

### Python frameworks

| Signal | Framework |
|--------|-----------|
| `from flask import` or `import flask` | Flask |
| `from fastapi import` or `import fastapi` | FastAPI |
| `import django` or `django.setup()` or `settings.py` with `INSTALLED_APPS` | Django |
| `from aiohttp import web` | aiohttp |
| `from bottle import` | Bottle |

### JavaScript / TypeScript frameworks

| Signal | Framework |
|--------|-----------|
| `require('express')` or `import express` | Express.js |
| `require('fastify')` or `import fastify` | Fastify |
| `require('koa')` or `import Koa` | Koa |
| `require('hapi')` or `import Hapi` | Hapi |
| `next.config.js` or `pages/` directory with `_app.js` | Next.js |
| `nuxt.config.js` | Nuxt.js |

### Java / Other

| Signal | Framework |
|--------|-----------|
| `@SpringBootApplication` annotation | Spring Boot |
| `@Path` or `@GET` JAX-RS annotations | JAX-RS / Quarkus |
| `Application extends ResourceConfig` | Jersey |

### Config file signals (supplement the above)

- `wsgi.py` or `asgi.py` → Python web app
- `Procfile` with `web:` → web server deployment
- `Dockerfile` with `EXPOSE` → containerized service
- `.env.example` or `.env` → environment-variable-driven config

---

## 3. Database Layer Mapping

### Python

| Signal | Database / Layer |
|--------|-----------------|
| `import sqlite3` | SQLite, raw queries |
| `import psycopg2` or `import psycopg` | PostgreSQL, raw queries |
| `import pymysql` or `import mysql.connector` | MySQL, raw queries |
| `from sqlalchemy` or `import sqlalchemy` | SQLAlchemy ORM |
| `from flask_sqlalchemy` | Flask-SQLAlchemy |
| `from peewee import` | Peewee ORM |
| `from tortoise` | Tortoise ORM (async) |
| `import motor` or `import pymongo` | MongoDB |
| `import redis` | Redis |
| `*.sql` files or `migrations/` directory | Raw schema / migrations |
| `alembic.ini` or `alembic/` directory | Alembic migrations |

### JavaScript / TypeScript

| Signal | Database / Layer |
|--------|-----------------|
| `require('pg')` or `import pg` | PostgreSQL, raw queries |
| `require('mysql')` or `require('mysql2')` | MySQL, raw queries |
| `require('better-sqlite3')` or `require('sqlite3')` | SQLite, raw queries |
| `require('sequelize')` or `import { Sequelize }` | Sequelize ORM |
| `require('mongoose')` or `import mongoose` | Mongoose / MongoDB |
| `require('typeorm')` or decorators `@Entity`, `@Column` | TypeORM |
| `require('prisma')` or `prisma/schema.prisma` | Prisma |
| `require('knex')` | Knex.js query builder |
| `drizzle.config.ts` or `import { drizzle }` | Drizzle ORM |

### Schema file detection

Look for:
- Files named `schema.sql`, `init.sql`, `seed.sql`, `create_tables.sql`
- Directories: `migrations/`, `db/`, `database/`, `schema/`
- ORM model files: classes that inherit from `db.Model`, `Base`, `Model`, `Entity`

---

## 4. Architecture Classification

Classify the project into one of three tiers based on how files are organized:

### Tier 1 — Flat / Monolithic

**Signals:**
- All code in a small number of files at the root level (e.g., `app.py`, `index.js`, `main.go`)
- Route definitions, business logic, and database queries mixed in the same functions
- No subdirectories beyond perhaps `static/` or `templates/`
- Single file with > 300 lines containing multiple responsibilities

**Label:** `Flat / Monolithic`

### Tier 2 — Partially Organized

**Signals:**
- Some separation of concerns attempted (e.g., separate `models.py` and `routes.py`) but incomplete
- Business logic still bleeds across layers (e.g., SQL in route handlers, or HTTP objects in model functions)
- Missing at least one of: dedicated controller layer, config module, error handler

**Label:** `Partially Organized`

### Tier 3 — MVC / Layered

**Signals:**
- Clear directory structure: `models/`, `controllers/` (or `services/`), `routes/` (or `views/`)
- Each layer has a single responsibility
- Config is centralized (not scattered)
- Entry point only wires the application together

**Label:** `MVC / Layered`

---

## 5. Counting Files, LOC, and Models/Tables

### File count

Count all source files (exclude: `node_modules/`, `__pycache__/`, `.git/`, `*.pyc`, `dist/`, `build/`, `venv/`, `.env`).

```
total_files = count of .py / .js / .ts / .java / .go / .rb / .php files
```

### LOC estimate

For each source file, count non-empty, non-comment lines. Sum across all files for an estimate. Prefix with `~` to indicate it is approximate.

If exact counting is slow, use file sizes as a proxy: a typical source file averages ~30–50 lines per KB.

### Models / Tables

Count:
- Classes that inherit from an ORM base (`db.Model`, `Base`, `Entity`, `Model`)
- SQL `CREATE TABLE` statements in schema files
- Mongoose `Schema` definitions
- Prisma `model` blocks

Report as: `<N> models/tables`

---

## 6. Domain Detection

Infer the business domain by reading:

1. **Endpoint paths**: `/users`, `/orders`, `/products`, `/invoices`, `/patients`, `/tickets`
2. **Model/table names**: `User`, `Order`, `Product`, `Customer`, `Employee`, `Article`
3. **Function names**: `create_order`, `process_payment`, `send_notification`
4. **README**: if present, read the first paragraph

Common domain patterns:

| Signals | Domain |
|---------|--------|
| `products`, `orders`, `cart`, `inventory`, `payment` | E-commerce / retail platform |
| `users`, `posts`, `comments`, `likes`, `feed` | Social network / content platform |
| `tasks`, `projects`, `assignments`, `deadlines` | Task / project management |
| `patients`, `appointments`, `doctors`, `prescriptions` | Healthcare management |
| `employees`, `departments`, `salaries`, `timesheet` | HR / payroll system |
| `invoices`, `clients`, `transactions`, `accounts` | Financial / billing system |
| `tickets`, `events`, `venues`, `bookings` | Event / ticketing platform |
| `students`, `courses`, `grades`, `enrollments` | Education / LMS |

Summarize in 1–2 sentences: what the system is and what it manages.

---

## Expected Output Format

At the end of Phase 1, print exactly:

```
## Phase 1: Project Analysis
- Language      : <e.g., Python 3>
- Framework     : <e.g., Flask>
- Database      : <e.g., SQLite via sqlite3 (raw queries, no ORM)>
- Architecture  : <e.g., Partially Organized>
- Files         : <N> | LOC: ~<N> | Models/Tables: <N>
- Domain        : <e.g., E-commerce platform managing products, orders, and users>
```

If any field cannot be determined, write `unknown — <best guess and reason>`.
