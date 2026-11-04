# Installer dependencies
`uv sync --project backend --all-extras`

# Launch the API
`uv run --project backend python backend/src/main.py`

# Launch tests
`uv run --project backend pytest backend/tests -v`
