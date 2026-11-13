# à améliorer plus tard pour avoir peut etre le meme init_db_sql pour nos tables principales et de tests
import os
from pathlib import Path

import pytest

from dao.db_connection import DBConnection
from utils.env_variables import load_environment_variables


@pytest.fixture(scope="session")
def connexion_test():
    """Prépare une connexion et une table Person réservées aux tests"""

    load_environment_variables()

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
                ALTER TABLE project_test_dao.person
                ADD COLUMN IF NOT EXISTS access_token_hash VARCHAR(64),
                ADD COLUMN IF NOT EXISTS access_token_expires_at TIMESTAMPTZ
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_test_dao.redacteddoc (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pii_count INT DEFAULT 0,
                    pii_positions VARCHAR(1000),
                    author_email VARCHAR(100),
                    params VARCHAR(1000)
                )
            """)

            cursor.execute("DELETE FROM redacteddoc;")
            cursor.execute("DELETE FROM person;")


    with connection.cursor() as cursor:
        cursor.execute("SELECT current_schema() AS schema")
        result = cursor.fetchone()

    assert result["schema"] == "project_test_dao"
    connection.rollback()

    yield connection
