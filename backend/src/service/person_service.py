from business_object.person import Person
from dao.person_dao import PersonDAO
from utils.security import hash_password


class PersonService:

    def login(self, email: str, password: str) -> Person | None:
        """Authentifie un utilisateur à partir de son email et de son mot de passe."""

        person = PersonDAO().find_by_email(email)

        if person is None:
            return None

        if hash_password(password) != person.password:
            return None

        return person