# 03 — Audit Report Template

Reference file for Phase 2 of the refactor-arch skill. Populate this template with the findings from your scan. Replace every `<placeholder>` with actual values. Do not omit sections, even if a severity tier has zero findings (write "None found").

---

## TEMPLATE — copy, fill in, and print

---

```
# Security & Quality Audit Report

## Project Metadata
| Field         | Value                          |
|---------------|--------------------------------|
| Project       | <project name or directory>    |
| Language      | <e.g., Python 3>               |
| Framework     | <e.g., Flask>                  |
| Database      | <e.g., SQLite (raw queries)>   |
| Files scanned | <N>                            |
| LOC           | ~<N>                           |
| Scan date     | <today's date>                 |

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | <N>   |
| HIGH     | <N>   |
| MEDIUM   | <N>   |
| LOW      | <N>   |
| **TOTAL**| **<N>**|

<1–3 sentence overview of the most significant issues found. Highlight any CRITICAL findings immediately.>

---

## Findings

### CRITICAL

---

#### [C1] <Pattern Name>

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | CRITICAL                           |
| Pattern        | P<NN> — <Pattern Name>             |
| Location       | `<file_path>` lines <start>–<end>  |

**Description:**
<What specifically is happening in this code. Be concrete: quote the problematic line or pattern.>

**Impact:**
<Copy from the catalog, or adapt to describe the specific risk in this codebase.>

**Recommendation:**
<Specific fix for this occurrence. Reference the playbook pattern number if applicable (e.g., "Apply Playbook P1: SQL Injection → Parameterized Queries").>

---

#### [C2] <Pattern Name>

<repeat structure above>

---

### HIGH

---

#### [H1] <Pattern Name>

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | HIGH                               |
| Pattern        | P<NN> — <Pattern Name>             |
| Location       | `<file_path>` lines <start>–<end>  |

**Description:**
<Concrete description.>

**Impact:**
<Impact text.>

**Recommendation:**
<Specific fix.>

---

<repeat for H2, H3, ...>

---

### MEDIUM

---

#### [M1] <Pattern Name>

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | MEDIUM                             |
| Pattern        | P<NN> — <Pattern Name>             |
| Location       | `<file_path>` lines <start>–<end>  |

**Description:**
<Concrete description.>

**Impact:**
<Impact text.>

**Recommendation:**
<Specific fix.>

---

<repeat for M2, M3, ...>

---

### LOW

---

#### [L1] <Pattern Name>

| Field          | Value                              |
|----------------|------------------------------------|
| Severity       | LOW                                |
| Pattern        | P<NN> — <Pattern Name>             |
| Location       | `<file_path>` lines <start>–<end>  |

**Description:**
<Concrete description.>

**Impact:**
<Impact text.>

**Recommendation:**
<Specific fix.>

---

<repeat for L2, L3, ...>

---

## Footer

**Total findings: <N>** (<CRITICAL_N> critical / <HIGH_N> high / <MEDIUM_N> medium / <LOW_N> low)

**Priority action plan:**
1. Fix all CRITICAL findings before deploying to any environment
2. Fix all HIGH findings before accepting user traffic
3. Schedule MEDIUM findings for the next sprint
4. Address LOW findings during regular maintenance
```

---

## Formatting rules

- **One finding per block.** Do not combine multiple occurrences of the same pattern across different files into a single finding — each distinct location gets its own block.
- **Consecutive IDs.** Number findings C1, C2, C3... H1, H2... M1, M2... L1, L2... within their severity tier.
- **Exact locations.** Always include the file path and line range. "somewhere in models.py" is not acceptable.
- **Concrete descriptions.** Quote or paraphrase the actual problematic code. "This file has SQL injection" is not acceptable; "Line 23: `cursor.execute(\"SELECT * FROM users WHERE id = \" + str(id))` concatenates an unsanitized integer" is acceptable.
- **No padding.** If a severity tier has zero findings, write the tier header and then: `None found.` Do not skip the tier.
- **Verify manually flag.** If you are uncertain whether something is a true positive, include the finding and add "(verify manually)" at the end of the description.
