---
name: refactor-arch
description: Analyzes legacy codebases for security vulnerabilities and architectural anti-patterns, then refactors them into clean MVC structure. Use this skill whenever the user wants to audit, analyze, or refactor a legacy project — even if they say things like "check my code", "find problems in this project", "clean up this codebase", "refactor this to MVC", "security audit", or "what's wrong with this code". This skill is proactive: trigger it even when the user doesn't know what they need but their project looks like legacy code.
---

# refactor-arch

Autonomous 3-phase pipeline: analyze a legacy codebase, audit it for security and quality issues, then refactor it into clean MVC architecture.

## How this skill works

You execute three sequential phases. Phases 1 and 2 are **read-only** — you explore and report, never modify files. Phase 3 rewrites the codebase and requires explicit user confirmation before it starts.

Each phase has reference files with detailed heuristics and templates. Read them when directed below.

---

## Phase 1: Project Analysis

Read `01-project-analysis.md` before starting this phase.

**What to do:**

1. List the project directory tree (top level first, then recurse into subdirectories)
2. Apply the detection heuristics in `01-project-analysis.md` to identify:
   - Programming language
   - Framework
   - Database layer (driver, ORM, schema files)
   - Current architecture style (flat/monolithic, partially organized, or MVC)
3. Count: total files, estimated lines of code, number of models/tables
4. Infer the business domain from endpoint names, model names, and table names

**Phase 1 output** — print this block before continuing:

```
## Phase 1: Project Analysis
- Language      : <detected>
- Framework     : <detected>
- Database      : <detected>
- Architecture  : <detected>
- Files         : <N> | LOC: ~<N> | Models/Tables: <N>
- Domain        : <1–2 sentence description of what this system does>
```

---

## Phase 2: Security & Quality Audit

Read `02-anti-patterns-catalog.md` and `03-audit-report-template.md` before starting this phase.

**What to do:**

1. Scan every relevant file for each of the 14 anti-patterns listed in `02-anti-patterns-catalog.md`
   - Use the detection signals from the catalog to find occurrences
   - Record: file path, line numbers, severity, which pattern
2. Remove duplicates where the same issue appears at the same location
3. Sort all findings: CRITICAL first, then HIGH, MEDIUM, LOW
4. Render the complete audit report using the template in `03-audit-report-template.md`

**Phase 2 output:** The full populated audit report, printed to console.

---

## MANDATORY PAUSE — Do not proceed past this point without user confirmation

After printing the Phase 2 report, stop and present this message exactly:

```
---
Phase 2 complete. The audit report above details all findings.

Phase 3 will restructure the codebase into MVC architecture and fix all CRITICAL
and HIGH severity findings. This will create new files and modify existing ones.

Do you want to proceed with Phase 3 (refactoring)? [yes / no]
---
```

**Wait for the user's response. Only continue if they say yes (or equivalent affirmative). If they say no, summarize what Phase 3 would have done and stop.**

---

## Phase 3: Refactoring

Read `04-mvc-architecture.md` and `05-refactoring-playbook.md` before starting this phase.

**What to do:**

### 3a — Plan first, write second

Before touching any files, print the planned target structure:

```
## Phase 3 Plan — Target Structure
<directory tree of the refactored project, showing every new file>

## Mapping (old → new)
<table or list: each existing file/function → which new file it goes to>
```

### 3b — Apply transformations

Work through the findings from Phase 2 in severity order:

1. **CRITICAL first**: SQL injection → parameterized queries; hardcoded credentials → env vars; insecure hashing → bcrypt/argon2
2. **HIGH next**: god classes → split into modules; business logic in routes → controller layer; missing auth → add middleware; sensitive data in responses → filter output fields
3. **MEDIUM/LOW where touched**: apply relevant transformations from `05-refactoring-playbook.md` on any file already being modified

Use the before/after examples in `05-refactoring-playbook.md` as the transformation reference for each pattern.

### 3c — Write the refactored files

Follow the directory structure from `04-mvc-architecture.md` for the detected stack:

- **Models layer**: data access only — queries, schema, no business logic
- **Controllers layer**: business logic, validation, orchestration
- **Routes/Views layer**: HTTP parsing only — reads request, calls controller, returns response
- **Config module**: all environment variables and settings in one place
- **Error handler**: centralized middleware, not scattered try/except blocks
- **Entry point**: wires everything together, contains no business logic itself

### 3d — Preserve functionality

All endpoints that existed before must still work after refactoring. Do not remove or rename endpoints unless the code is provably dead (never called, no tests referencing it).

### Validation checklist

Before declaring Phase 3 complete, verify each item:

- [ ] No hardcoded credentials in any file (passwords, secret keys, API keys, tokens)
- [ ] All SQL queries use parameterized form — no string concatenation with user-controlled input
- [ ] No MD5 or SHA1 used for password hashing
- [ ] Route handlers contain no business logic (only HTTP parsing + delegation to controller)
- [ ] Each file has one clear responsibility
- [ ] Sensitive fields (passwords, tokens, secrets) are excluded from all API responses
- [ ] All config values come from environment variables
- [ ] Entry point only wires dependencies — zero business logic
- [ ] Error handling is centralized in one place

**Phase 3 output** — print this block when done:

```
## Phase 3: Refactoring Complete

### New Structure
<directory tree>

### Fixes Applied
- CRITICAL : <N> fixed
- HIGH     : <N> fixed
- MEDIUM   : <N> fixed
- LOW      : <N> fixed

### Validation
<checklist — mark each item PASS or FAIL, with a note on any FAILs>
```

---

## When something is unclear

- If you cannot determine the language or framework in Phase 1: state "unknown", note your best guess and why, and proceed.
- If a finding in Phase 2 might be a false positive: include it and mark it "(verify manually)".
- If a transformation in Phase 3 requires context you don't have: skip it, note it in the Phase 3 summary as "requires manual review", and do not guess at the intent of the code.
- If no target directory is specified: operate on the current working directory.
