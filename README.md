# Anonymia (2A computer science project, ENSAI, Team 21)

An application for redacting personal data (PII) from administrative documents.

Two detectors run in parallel: regular expressions for fixed formats (social security numbers, IBANs, email addresses, phone numbers, etc.) and an LLM hosted on SSPCloud for free-form data (names, addresses, locations, etc.). Their results are merged, then masked or pseudonymised.

The API is built with FastAPI, and the user interface with Streamlit.

## Features

| | What the application does |
|---|---|
| F1 | Login with email and password (Argon2 hash), 24-hour revocable session token, three roles. After 5 failed logins in 15 minutes for the same address, it is blocked for 15 minutes (HTTP 429). The administrator creates, changes the role of, deactivates or reactivates, and deletes accounts. |
| F2 | Detection by 13 regular expressions and by the LLM, run in parallel, then merged. Each item comes with its position, type, confidence and detector. If the LLM fails, the regex results are used and the failure is reported. |
| F3 | Masking (`[NAME_1]`, `[NIR_1]`...) or consistent pseudonymisation (the same value always gets the same substitute within a document). |
| F4 | Audit log of every processing: date, author, HMAC fingerprint of the document (never its content), number, types and positions of detected items, options. Supervisors and administrators browse it with filters and charts. |
| F5 | Strict system prompt and forced JSON output, injection filter before the call (the document is refused, HTTP 400), verification of the LLM answer (invented items removed, suspicious omission reported). |
| FO2 | Optional direct rewrite by the LLM (`POST /doc/redact_llm/`), shown next to the regular result for comparison. Not logged, not offered for download. |
| FO3 | When the LLM is enabled, a second LLM call judges in parallel whether the document tries to manipulate the model. The verdict (`sain`, `suspect` or `indisponible`) is stored in the audit log; a suspicious document is still redacted, but the user is warned and the attempt is recorded. |
| FO4 | Highlighted source text, side-by-side comparison of the detectors with counts per type, activity charts in the history page. |

## Requirements

- A Python VS Code service on Onyxia (SSPCloud), with this repository cloned into `~/work`;
- A PostgreSQL service running on Onyxia;
- A personal API key for the SSPCloud LLM API.

## Configuration

Copy the configuration template, then fill it in:

```bash
cp .env.example .env
```

The `.env` file is never committed to version control. It must contain:

| Variable | Value |
|---|---|
| `LLM_BASE_URL` | `https://llm.lab.sspcloud.fr/api` |
| `SSPCLOUD_API_KEY` | Your personal API key |
| `LLM_MODEL` | `gemma4-26b-moe` (model chosen after comparison, see below) |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | See the PostgreSQL service README on Onyxia |
| `POSTGRES_SCHEMA` | `anonymia` |
| `DOC_HASH_SECRET` | HMAC key used to fingerprint documents (F4). See below |

### The `DOC_HASH_SECRET` key

Document fingerprints are computed with HMAC-SHA256 and this secret key. Without it, redaction is refused. Two cases:

- **Joining the team** (shared database): ask a team member for the key, in a private message. Never commit it, and never regenerate it: fingerprints already stored could no longer be compared with new ones.
- **New installation with its own database** (for example, to evaluate the project): generate your own key and paste it after `DOC_HASH_SECRET=` in `.env`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Installation

From the repository root:

```bash
uv sync --project backend --all-extras
```

## Running the API

From the repository root:

```bash
uv run --project backend uvicorn main:app --app-dir backend/src --port 5000 --root-path /proxy/5000
```

The interactive documentation is then available from the **Ports** tab in VS Code (port 5000), by appending `/docs` to the URL.

### First use on a new database

The `GET /reset_database` route requires an administrator token, so it cannot be used before any account exists. On a new database, create the tables and the test accounts directly. From the repository root, go to the source folder:

```bash
cd backend/src
```

Then run the reset script (it creates the tables, inserts the test accounts and hashes their passwords):

```bash
uv run --project .. python -c "from utils.reset_database import ResetDatabase; ResetDatabase().run()"
```

Go back to the repository root afterwards (`cd ../..`). Later resets can be done from the API with `GET /reset_database`, logged in as an administrator.

### Database created before account deactivation was added

Account deactivation (F1) adds an `active` column to the `person` table. A database created before this change must be migrated once, otherwise the API cannot read the accounts. From the `backend/src` folder:

```bash
uv run --project .. python -c "from dao.db_connection import DBConnection; c = DBConnection().connection; c.cursor().execute(open('../../data/migration_desactivation.sql').read()); c.commit()"
```

Existing accounts stay active. A reset (`ResetDatabase().run()` or `GET /reset_database`) also creates the column, but erases all data.

## Running the user interface

In a second terminal, from the repository root, while the API is still running in the first one:

```bash
uv run --project frontend streamlit run frontend/app.py --server.port 8501
```

The user interface is then available from the **Ports** tab in VS Code (port 8501).

## Roles

| Role | Access |
|---|---|
| User | Redact documents (with the detector comparison and the optional direct LLM rewrite), change their own password |
| Supervisor | Same as User, plus the processing history (audit log) with filters and charts |
| Administrator | Same as Supervisor, plus account management (create, change role, deactivate or reactivate, delete) |

## Test accounts

| Email | Password | Role |
|---|---|---|
| `a@a.com` | `a` | User |
| `b@b.com` | `b` on a new installation (ask the group for the shared database) | Administrator |

After 5 wrong passwords in 15 minutes, an address is blocked for 15 minutes. The counters are kept in memory: restarting the API also clears them.

If the interface says the email or password is wrong although they are right, check `backend/logs/backend.log`: the interface shows this message for every API error, including an unreachable database (restart the PostgreSQL service in Onyxia).

## Running the tests

Unit tests (the ones run by GitHub on every push, no database needed):

```bash
uv run --project backend pytest backend/tests/test_business_object backend/tests/test_service -m "not llm"
```

DAO tests write to the database, so they refuse to run on the production schema. Before running them, set `POSTGRES_SCHEMA=project_test_dao` in `.env`, then set it back to `anonymia` afterwards:

```bash
uv run --project backend pytest backend/tests/test_dao
```

Coverage on 24 November 2026: 85 % with unit tests only (216 cases), 93 % including DAO tests (244 cases). Add `--cov=backend/src --cov-report=term` to measure it.

The test marked `llm` calls the real model; run it with `-m llm`.

## Tutor corpus

`backend/tests_tuteur/` contains the 68 annotated documents provided by the tutor and the evaluation script `test_complet.py`. It calls the real LLM. From the `backend/src` folder:

```bash
uv run --project .. python ../tests_tuteur/test_complet.py
```

Results on 24 November 2026 (regex + `gemma4-26b-moe`): recall 94 % on circle 1 (direct identifiers), 86 % on circle 2, 37 % on circle 3 (sensitive or contextual data), 82 % overall and 90 % without the internal file numbers and public figures that our rules deliberately leave visible; precision 98 %.

The injection defences were measured on the same corpus with `backend/scripts/evaluer_juge.py` (one run, `gemma4-26b-moe`): the pattern filter blocks 2 of the 17 trap documents, while the injection judge (FO3) flags all 17, including the 15 the filter misses, with no false alarm on the 51 other documents. From the repository root:

```bash
uv run --project backend python backend/scripts/evaluer_juge.py
```

## Model comparison

`backend/scripts/comparer_modeles.py` compares the SSPCloud text models on a fixed, hand-annotated test set (recall first, under a precision constraint, 3 runs per model):

```bash
uv run --project backend python backend/scripts/comparer_modeles.py
```

Results on 24 November 2026 (8 texts, 32 personal data items, 3 runs):

| Configuration | Mean recall | Precision | Time for 8 texts |
|---|---|---|---|
| Regex + LLM (qwen3-8-27b) | 100 % | 100 % | 54 s |
| Regex + LLM (gemma4-26b-moe) | 97 % | 100 % | 5 s |
| Regex + LLM (qwen3-6-35b-moe) | 97 % | 100 % | 78 s |
| Regex only | 19 % | 100 % | < 1 s |

`gemma4-26b-moe` was chosen as the default model: nearly the same recall, about ten times faster.

## Disclaimer

Neither detector has 100 % recall: some personal data may go undetected.

Human review remains mandatory before distributing any redacted document.