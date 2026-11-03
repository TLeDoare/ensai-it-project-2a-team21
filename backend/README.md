# Installer les dépendances
`uv sync --project backend --all-extras`

# Lancer l'API
`uv run --project backend python backend/src/main.py`

# Lancer les tests
`uv run --project backend pytest backend/tests`
