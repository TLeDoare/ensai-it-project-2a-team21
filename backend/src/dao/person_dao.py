from datetime import datetime
from hashlib import sha256

from business_object.person import Person
from business_object.types import Role
from dao.db_connection import DBConnection


class PersonDAO:

    def _build_person(self, result: dict) -> Person:
        """Construit un objet Person à partir d'une ligne de la BDD."""
        return Person(
            id=result["id"],
            email=result["email"],
            password=result["password"],
            role=Role[result["role"].capitalize()],
        )

    def find_by_id(self, id: int) -> Person | None:
        """Recherche un utilisateur à partir de son adresse email."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, role
                    FROM Person
                    WHERE id = %s
                    """,
                    (id,),
                )
                result = cursor.fetchone()

        if result is None:
            return None

        return self._build_person(result)

    def find_by_email(self, email: str) -> Person | None:
        """Recherche un utilisateur à partir de son adresse email."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, role
                    FROM Person
                    WHERE email = %s
                    """,
                    (email,),
                )
                result = cursor.fetchone()

        if result is None:
            return None

        return self._build_person(result)

    def find_by_token(self, token: str) -> Person | None:
        """Recherche un utilisateur à partir de son token d'accès."""

        token_hash = sha256(token.encode("utf-8")).hexdigest()

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, role
                    FROM Person
                    WHERE access_token_hash = %s
                      AND access_token_expires_at > CURRENT_TIMESTAMP
                    """,
                    (token_hash,),
                )
                result = cursor.fetchone()

        if result is None:
            return None

        return self._build_person(result)

    def find_all(self) -> list[Person]:
        """List all players in the database.
        Returns:
            list[Person]
        """

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, password, role        "
                    "  FROM Person                           "
                )
                res = cursor.fetchall()

        return [self._build_person(row) for row in res]

    def update_access_token(self, person_id: int, access_token: str, expires_at: datetime) -> None:
        """Met à jour le token d'accès d'un utilisateur."""

        token_hash = sha256(access_token.encode("utf-8")).hexdigest()

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Person
                    SET access_token_hash = %s,
                        access_token_expires_at = %s,
                        access_token = NULL
                    WHERE id = %s
                    """,
                    (token_hash, expires_at, person_id),
                )

    def create(self, person: Person) -> Person:
        """Crée un nouvel utilisateur dans la base de données."""

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Person (email, password, role)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        person.email,
                        person.password,
                        person.role.name.lower(),
                    ),
                )

                result = cursor.fetchone()

        person.id = result["id"]

        return person

    def update(self, person: Person) -> bool:
        """Met à jour les informations de l'utilisateur."""

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Person
                    SET role = %(role)s,
                        password = COALESCE(%(password)s, password),
                        email = %(email)s
                    WHERE id = %(id)s
                    """,
                    {
                        "password": person.password,
                        "email": person.email,
                        "id": person.id,
                        "role": person.role.name.lower(),
                    },
                )

                nb_affected_rows = cursor.rowcount

        return nb_affected_rows == 1
