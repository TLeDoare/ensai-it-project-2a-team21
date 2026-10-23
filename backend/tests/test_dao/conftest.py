# à améliorer plus tard pour avoir peut etre le meme init_db_sql pour nos tables principales et de tests 
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from dao.db_connection import DBConnection


@pytest.fixture(scope="session")
def connexion_test():
    """Prépare une connexion et une table Person réservées aux tests."""

    # GIVEN : charger la configuration locale
    backend_dir = Path(__file__).resolve().parents[2]
    env_path = backend_dir / ".env"

    if not env_path.is_file():
        pytest.fail("Fichier backend/.env introuvable.")

    load_dotenv(env_path, override=True)

    if os.getenv("POSTGRES_SCHEMA") != "project_test_dao":
        pytest.fail("Le schéma PostgreSQL n'est pas celui des tests.")

    connection = DBConnection().connection

    # Vérifier la destination AVANT de modifier la BDD
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database() AS db")
        config = cursor.fetchone()

    host = connection.get_dsn_parameters().get("host")

    if config["db"] != "anonymia_test":
        pytest.fail("La connexion ne pointe pas vers anonymia_test.")

    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("La connexion PostgreSQL n'est pas locale.")

    # WHEN : préparer le schéma et la table de test
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE SCHEMA IF NOT EXISTS project_test_dao"
            )

            cursor.execute(
                "SET search_path TO project_test_dao"
            )

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_test_dao.person (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(25) NOT NULL,
                    access_token VARCHAR(50)
                )
            """)

    # THEN : vérifier le schéma actif
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_schema() AS schema")
        result = cursor.fetchone()

    assert result["schema"] == "project_test_dao"
    connection.rollback()

    yield connection
