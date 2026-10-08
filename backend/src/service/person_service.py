import secrets

from business_object.person import Person
from business_object.types import Role
from dao.person_dao import PersonDAO
from utils.security import hash_password, verify_password


class PersonService:

    def create(self, email: str, password: str, role: Role) -> Person | None:
        """Crée un nouvel utilisateur."""

        dao = PersonDAO()

        # L'email doit être unique
        if dao.find_by_email(email) is not None:
            return None

        hashed_password = hash_password(password)

        person = Person(
            email=email,
            password=hashed_password,
            role=role,
        )

        return dao.create(person)

    def login(self, email: str, password: str) -> Person | None:
        """Authentifie un utilisateur à partir de son email et de son mot de passe."""

        person = PersonDAO().find_by_email(email)

        if person is None:
            return None

        if not verify_password(password, person.password):
            return None

        access_token = secrets.token_urlsafe(32)

        PersonDAO().update_access_token(person.id, access_token)

        person.access_token = access_token

        return person