# Anonymia backend

FastAPI application that detects and redacts personal data (PII) in documents. Every feature is reachable over HTTP; the Streamlit interface in `frontend/` is only a client of this API. Installation and launch are described in the README at the repository root; this file describes the code and the development tools.

## Layered architecture

Requests always go down the layers in the same order, and each layer only calls the one below it.

```
controller  ->  service  ->  business_object
                   |
                   v
                  dao  ->  PostgreSQL
```

| Folder (`src/`) | Role |
|---|---|
| `main.py` | Creates the FastAPI application, registers the routers (`/login`, `/person`, `/doc`) and the `GET /reset_database` route. Can also be run directly from the repository root: `uv run --project backend python backend/src/main.py`. |
| `controller/` | HTTP layer: one router per resource. Checks the session token (`x-auth-token` header), validates input with the Pydantic models of `schema/`, calls a service and turns business exceptions into HTTP codes (400, 401, 403, 404, 409, 413, 415, 429). |
| `schema/` | Pydantic models for requests and responses (`PersonModel`, `DocModel`). |
| `service/` | Application rules: `PersonService` (login, login attempt limit, tokens, accounts, rights matrix in `grant_auth`) and `DocService` (injection filter, analysis, injection judge, redaction, audit log). |
| `business_object/` | Entities (`Person`, `RedactedDoc`, enums in `types.py`) and algorithms, with no HTTP or SQL: `analyser/` (Decorator pattern: `LLMDecorator(RegexDecorator(EmptyAnalyser()))`, built by `AnalyserFactory`; overlap merge in `overlap.py`), `llm_client/` (SSPCloud client, prompts, `InjectionFilter`, `OutputVerifier`, `InjectionJudge`), `redactor/` (Strategy pattern: masking or pseudonymisation, chosen through `RedactorContext`). |
| `dao/` | All SQL queries, with bound parameters only: `PersonDAO`, `DocDAO`, `InjectionAttemptDAO`. `DBConnection` is a singleton holding the PostgreSQL connection. |
| `utils/` | Environment variables, exceptions, password and document hashing (`security.py`), login attempt limiter, logging helper, database reset. |

The database is created by `data/init_db.sql` (tables `person`, `redacteddoc`, `prompt_injection_attempt`) and filled with test accounts by `data/pop_db.sql`. Run them through `ResetDatabase` (see the root README), which also hashes the test passwords: running `pop_db.sql` alone in `psql` leaves plain-text passwords that cannot log in.

## Development tools

All commands are run from the repository root, after `uv sync --project backend --all-extras`.

### Tests

| Folder | Content | Needs |
|---|---|---|
| `tests/test_business_object` | Regex patterns, validators, overlap merge, LLM output verification, injection filter and judge, redactors, analyser chain | nothing |
| `tests/test_service` | Services with mocked DAOs (`@patch`), controllers through FastAPI's `TestClient` with `app.dependency_overrides`, rights matrix, login limit | nothing |
| `tests/test_dao` | Real SQL queries | PostgreSQL, with `POSTGRES_SCHEMA=project_test_dao` in `.env` |

Tests that call the real LLM carry the `llm` marker. GitHub Actions (`.github/workflows/tests.yml`) runs the first two folders on every push:

```bash
uv run --project backend pytest backend/tests/test_business_object backend/tests/test_service -m "not llm"
```

The DAO tests refuse to run on any other schema than `project_test_dao`, so they never touch real data. Set it in `.env`, run them, then set `POSTGRES_SCHEMA=anonymia` back:

```bash
uv run --project backend pytest backend/tests/test_dao
```

Coverage on 24 November 2026: 85 % without the DAO tests (216 cases), 93 % with them (244 cases):

```bash
uv run --project backend pytest backend/tests/test_business_object backend/tests/test_service -m "not llm" --cov=backend/src --cov-report=term
```

`tests_tuteur/` holds the tutor's annotated corpus (68 documents) and its evaluation script; `scripts/comparer_modeles.py` compares the SSPCloud models. Both call the real LLM (see the root README).

### Logs

Logging is configured in `logging_config.yml`. Every module gets its logger with `utils.log_utils.get_logger(__name__)`. Logs are written to `backend/logs/backend.log` (relative to the folder the API is started from, hence the repository root), with a new file every midnight. Nothing is printed to the terminal: check this file when the API answers with an error. Document contents are never written to the logs, and the secrets of `.env` are masked.

### Code quality

`ruff` (linter and import order, configured in `pyproject.toml`) and `bandit` (security scan) are installed with the `dev` extra:

```bash
uv run --project backend ruff check backend/src
```

```bash
uv run --project backend bandit -r backend/src
```
