import secrets

from psycopg2.errors import UniqueViolation

from business_object.person import Person
from business_object.types import Role
from dao.person_dao import PersonDAO
from utils.security import hash_any, verify_password
from utils.exceptions import PersonNotFound, AuthError, EmailAlreadyUsed


class PersonService:

    def create(self, email: str, password: str, role: Role, sent_by: int) -> Person | None:
        """Crée un nouvel utilisateur."""

        dao = PersonDAO()

        # L'email doit être unique
        if dao.find_by_email(email) is not None:
            return None

        hashed_password = hash_any(password)

        person = Person(
            email=email,
            password=hashed_password,
            role=role,
        )
        
        author = PersonDAO().find_by_id(sent_by)

        if author.role == Role.Administrateur:
            try:
                return dao.create(person)
            except UniqueViolation as u:
                raise EmailAlreadyUsed from u
        else:
            raise AuthError(Role.Administrateur)

    def find_all(self, sent_by: int):
        author = PersonDAO().find_by_id(sent_by)
        if author.role == Role.Administrateur or author.role == Role.Superviseur:
            persons = PersonDAO().find_all()
            if persons == []:
                raise PersonNotFound
            else:
                return persons
        else:
            raise AuthError(Role.Superviseur)

    def find_by_id(self, id: int, sent_by: int):
        author = PersonDAO().find_by_id(sent_by)
        if author.role == Role.Administrateur or author.role == Role.Superviseur:
            person = PersonDAO().find_by_id(id)
            if person is None:
                raise PersonNotFound
            else:
                return person
        else:
            raise AuthError(Role.Superviseur)

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
