# Installer dependencies
`uv sync --project backend --all-extras`

# Launch the API
`uv run --project backend python backend/src/main.py`

# Launch tests
`uv run --project backend pytest backend/tests -v`

# Coverage
`uv run --project backend coverage run -m pytest backend`
`uv run --project backend coverage report -m`
`uv run --project backend coverage html`
`cd htmlcov`
`python -m http.server`