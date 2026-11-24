# Anonymia (2A computer science project, ENSAI, Team 21)

An application for redacting personal data (PII) from administrative documents.

Two detectors run in parallel: regular expressions for fixed formats (social security numbers, IBANs, email addresses, phone numbers, etc.) and an LLM hosted on SSPCloud for free-form data (names, addresses, locations, etc.). Their results are merged, then masked or pseudonymised.

The API is built with FastAPI, and the user interface with Streamlit.

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
| User | Redact documents, change their own password |
| Supervisor | Same as User, plus the processing history (audit log) with filters and charts |
| Administrator | Same as Supervisor, plus account management (create, change role, deactivate or reactivate, delete) |

## Test accounts

| Email | Password | Role |
|---|---|---|
| `a@a.com` | `a` | User |
| `b@b.com` | `b` on a new installation (ask the group for the shared database) | Administrator |

## Running the tests

Unit tests (the ones run by GitHub on every push, no database needed):

```bash
uv run --project backend pytest backend/tests/test_business_object backend/tests/test_service -m "not llm"
```

DAO tests write to the database, so they refuse to run on the production schema. Before running them, set `POSTGRES_SCHEMA=project_test_dao` in `.env`, then set it back to `anonymia` afterwards:

```bash
uv run --project backend pytest backend/tests/test_dao
```

Coverage: about 81 % with unit tests only, 90 % including DAO tests. Add `--cov=backend/src --cov-report=term` to measure it.

The test marked `llm` calls the real model; run it with `-m llm`.

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