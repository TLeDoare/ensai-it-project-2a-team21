import secrets

from psycopg2.errors import UniqueViolation

from business_object.person import Person
from business_object.types import Access, Role
from dao.person_dao import PersonDAO
from utils.exceptions import AuthError, EmailAlreadyUsed, PersonNotFound, WrongCredError
from utils.security import hash_any, verify_password


class PersonService:

    def create(self, email: str, password: str, role: Role, sent_by: Person) -> Person | None:
        """Crée un nouvel utilisateur."""

        self.grant_auth(sent_by, Access.CreatePerson)

        dao = PersonDAO()

        # L'email doit être unique
        if dao.find_by_email(email) is not None:
            raise EmailAlreadyUsed

        hashed_password = hash_any(password)

        person = Person(
            email=email,
            password=hashed_password,
            role=role,
        )

        try:
            return dao.create(person)
        except UniqueViolation as u:
            raise EmailAlreadyUsed from u

    def find_all(self, sent_by: Person):
        self.grant_auth(sent_by, Access.ReadPerson)
        persons = PersonDAO().find_all()
        if persons == []:
            raise PersonNotFound
        else:
            return persons

    def find_by_id(self, id: int, sent_by: Person | None = None):
        # Si cette fonction est éxecutée par le serveur et non par une personne tierce, alors son auteur est None. Sinon,
        # on vérifie si l'auteur a le droit d'accéder aux utilisateurs. Ce n'est pas un problème car toute requête faite par un
        # utilisateur passe par le contrôleur, et le contrôleur fait appel à verify_token pour authentifier l'utilisateur qui ne
        # renvoie jamais None, seulement une erreur 401.
        if sent_by is not None:
            self.grant_auth(sent_by, Access.ReadPerson)
        person = PersonDAO().find_by_id(id)
        if person is None:
            raise PersonNotFound
        else:
            return person

    def update(self, person: Person, sent_by: Person):
        self.grant_auth(sent_by, Access.UpdatePerson, person)
        person.password = hash_any(person.password)
        PersonDAO().update(person)
        return person

    def grant_auth(self, who: Person, req: Access, third_p = None) -> None:
        access = False
        if req == Access.ReadDoc:
            access = who.role in (Role.Administrateur, Role.Superviseur)
        elif req == Access.CreateDoc:
            access = who.role in (Role.Administrateur, Role.Superviseur, Role.Utilisateur)
        elif req == Access.ReadPerson:
            access = who.role in (Role.Administrateur, Role.Superviseur)
        elif req == Access.CreatePerson:
            access = who.role == Role.Administrateur
        elif req == Access.UpdatePerson:
            access = who.id == third_p.id
        elif req == Access.DeletePerson:
            access = who.role == Role.Administrateur
        else:
            access = False

        if access:
            return None
        else:
            raise AuthError


    def login(self, email: str, password: str) -> Person | None:
        """Authentifie un utilisateur à partir de son email et de son mot de passe."""

        person = PersonDAO().find_by_email(email)

        if person is None:
            raise WrongCredError

        if not verify_password(password, person.password):
            raise WrongCredError

        access_token = secrets.token_urlsafe(32)

        PersonDAO().update_access_token(person.id, access_token)

        person.access_token = access_token

        return person
