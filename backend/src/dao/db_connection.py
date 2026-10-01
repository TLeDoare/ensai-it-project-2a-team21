import os

import psycopg2
from psycopg2.extras import RealDictCursor

from utils.singleton import Singleton


class DBConnection(metaclass=Singleton):
    """Database connection manager implementing the Singleton pattern.

    This class ensures that only a single connection to the PostgreSQL
    database is opened and shared throughout the application lifecycle.

    Attributes:
        connection (psycopg2.extensions.connection): The active database
            connection instance.
    """

    def __init__(self):
        """Initializes the database connection using environment variables.
        Raises:
            KeyError: If any of the required POSTGRES_* environment variables are missing.
            psycopg2.Error: If the connection to the database fails.
        """

        self.__connection = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            database=os.environ["POSTGRES_DATABASE"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            options=f"-c search_path={os.environ['POSTGRES_SCHEMA']}",
            cursor_factory=RealDictCursor,
        )

    @property
    def connection(self):
        """Provides access to the underlying database connection.
        Returns:
            The established database connection.
        """
        return self.__connection
