# à améliorer plus tard pour avoir peut etre le meme init_db_sql pour nos tables principales et de tests 
import os
from pathlib import Path

import pytest

from dao.db_connection import DBConnection


@pytest.fixture(scope="session")
def connexion_test():
    """Prépare une connexion et une table Person réservées aux tests"""

    backend_dir = Path(__file__).resolve().parents[2]
    env_path = backend_dir / ".env"

    if not env_path.is_file():
        pytest.fail("Fichier backend/.env introuvable.")

    load_dotenv(env_path, override=True)

    if os.getenv("POSTGRES_SCHEMA") != "project_test_dao":
        pytest.fail("Le schéma PostgreSQL n'est pas celui des tests.")

    connection = DBConnection().connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database() AS db")
        config = cursor.fetchone()

    host = connection.get_dsn_parameters().get("host")

    if config["db"] != "defaultdb":
        pytest.fail("La connexion ne pointe pas vers defaultdb.")

    if host != os.getenv("POSTGRES_HOST"):
        pytest.fail(f"La connexion PostgreSQL n'est pas locale; elle vaut {host}.")

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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_test_dao.redacteddoc (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pii_count INT DEFAULT 0,
                    pii_positions VARCHAR(1000),
                    params VARCHAR(1000),
                    hash_doc CHAR(64)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_test_dao.traitement (
                    id_person INT NOT NULL,
                    id_doc INT NOT NULL,
                    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id_person, id_doc),
                    FOREIGN KEY (id_person)
                        REFERENCES project_test_dao.person(id) ON DELETE CASCADE,
                    FOREIGN KEY (id_doc)
                        REFERENCES project_test_dao.redacteddoc(id) ON DELETE CASCADE
                )
            """)

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_schema() AS schema")
        result = cursor.fetchone()

    assert result["schema"] == "project_test_dao"
    connection.rollback()

    yield connection
