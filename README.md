# Anonymia (2A computer science project, ENSAI, Team 21)

An application for redacting personal data from administrative documents.

Two detectors work in parallel: regular expressions for fixed formats (social security numbers, IBANs, email addresses, phone numbers, etc.) and an LLM for free-form data (names, addresses, locations, etc.).

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

The `.env` file (never committed to version control) must contain:

| Variable | Value |
|---|---|
| `LLM_BASE_URL` | `https://llm.lab.sspcloud.fr/api` |
| `SSPCLOUD_API_KEY` | Your personal API key |
| `LLM_MODEL` | `gemma4-26b-moe` |
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | See the PostgreSQL service README on Onyxia |
| `POSTGRES_SCHEMA` | Any name of your choice, e.g. `anonymia` |

## Installation

From the repository root:

```bash
uv sync --project backend --all-extras
```

## Running the API

```bash
uv run --project backend uvicorn main:app --app-dir backend/src --port 5000 --root-path /proxy/5000
```

The `--root-path /proxy/5000` option is required on Onyxia; otherwise, the documentation page will fail to load ("Failed to load API definition").

The interactive documentation is then accessible from the **Ports** tab in VS Code (port 5000), by appending `/docs` to the URL.

On first use, call `GET /reset_database` to create the tables and test accounts.

## Running the user interface

In a second terminal, while the API is still running in the first one:

```bash
cd frontend
uv run --project ../backend streamlit run app.py --server.port 8501
```

The user interface is accessible from the **Ports** tab in VS Code (port 8501).

## Test accounts

| Email | Password | Role |
|---|---|---|
| `a@a.com` | `a` | User |
| `b@b.com` | Ask the group | Administrator |

## Running the tests

```bash
uv run --project backend pytest backend/tests -v
```

## Disclaimer

Neither detector has 100% recall: some personal data may go undetected.

Human review remains mandatory before distributing any redacted document.