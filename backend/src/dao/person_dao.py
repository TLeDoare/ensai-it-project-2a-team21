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
            access_token=result["access_token"],
        )

    def find_by_id(self, id: int) -> Person | None:
        """Recherche un utilisateur à partir de son adresse email."""
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, role, access_token
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
                    SELECT id, email, password, role, access_token
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
        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password, role, access_token
                    FROM Person
                    WHERE access_token = %s
                    """,
                    (token,),
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
                    "SELECT *                                "
                    "  FROM Person                           "
                )
                res = cursor.fetchall()

        players_list = []

        if res:
            for row in res:
                player = Person(
                    id=row["id"],
                    email=row["email"],
                    password=row["password"],
                    role=row["role"],
                    access_token=row["access_token"],
                )

                players_list.append(player)

        return players_list

    def update_access_token(self, person_id: int, access_token: str) -> None:
        """Met à jour le token d'accès d'un utilisateur."""

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE Person
                    SET access_token = %s
                    WHERE id = %s
                    """,
                    (access_token, person_id),
                )

    def create(self, person: Person) -> Person:
        """Crée un nouvel utilisateur dans la base de données."""

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Person (email, password, role, access_token)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        person.email,
                        person.password,
                        person.role.name.lower(),
                        person.access_token,
                    ),
                )

                result = cursor.fetchone()

        person.id = result["id"]

        return person

    def update(self, person) -> bool:
        nb_affected_rows = 0

        with DBConnection().connection as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE Person                                                  "
                    "   SET role = %(role)s,                                "
                    "       password = COALESCE(%(password)s, password),            "
                    "       email = %(email)s,                                      "
                    "       access_token = COALESCE(%(access_token)s, access_token) "
                    " WHERE id = %(id)s;                              ",
                    {
                        "password": person.password,
                        "email": person.email,
                        "access_token": person.access_token,
                        "id": person.id,
                        "role": person.role
                    },
                )
                nb_affected_rows = cursor.rowcount

        return nb_affected_rows == 1
