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
| `DOC_HASH_SECRET` | HMAC key used to fingerprint documents (F4). Shared privately within the team; never regenerate it, or past fingerprints can no longer be compared |

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

On first use, call `GET /reset_database` to create the tables and test accounts.

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
| Administrator | Same as Supervisor, plus account management (create, change role, delete) |

## Test accounts

| Email | Password | Role |
|---|---|---|
| `a@a.com` | `a` | User |
| `b@b.com` | Ask the group | Administrator |

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

## Disclaimer

Neither detector has 100 % recall: some personal data may go undetected.

Human review remains mandatory before distributing any redacted document.