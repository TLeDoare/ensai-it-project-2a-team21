import secrets
from datetime import UTC, datetime, timedelta

from psycopg2.errors import UniqueViolation

from business_object.person import Person
from business_object.types import Access, Role
from dao.person_dao import PersonDAO
from utils.exceptions import (
    AccountDisabled,
    AuthError,
    EmailAlreadyUsed,
    PersonNotFound,
    TooManyAttempts,
    WrongCredError,
)
from utils.limiteur_connexion import limiteur_connexion
from utils.log_utils import get_logger
from utils.security import hash_any, verify_password

logger = get_logger(__name__)


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

    def change_role(self, id: int, role: Role, sent_by: Person) -> Person:
        """Change le rôle d'un compte (administrateur uniquement)."""
        if sent_by.role != Role.Administrateur:
            raise AuthError
        # Un administrateur ne modifie pas son propre rôle : évite de bloquer l'application sans administrateur
        if sent_by.id == id:
            raise AuthError
        person = self.find_by_id(id)
        person.role = role
        person.password = None  # COALESCE dans le DAO : le mot de passe existant est conservé
        PersonDAO().update(person)
        return person

    def delete(self, id: int, sent_by: Person) -> None:
        """Supprime un compte (administrateur uniquement, jamais son propre compte)."""
        self.grant_auth(sent_by, Access.DeletePerson)
        if sent_by.id == id:
            raise AuthError
        if not PersonDAO().delete(id):
            raise PersonNotFound

    def set_active(self, id: int, active: bool, sent_by: Person) -> Person:
        """Désactive ou réactive un compte (administrateur uniquement, jamais son propre compte).

        Un compte désactivé reste en base, avec son historique, mais ne peut plus se connecter.
        """
        self.grant_auth(sent_by, Access.DeletePerson)
        # Un administrateur ne se désactive pas lui-même : évite de bloquer l'application sans administrateur
        if sent_by.id == id:
            raise AuthError
        person = self.find_by_id(id)
        PersonDAO().set_active(id, active)
        person.active = active
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

        # Trop d'échecs récents pour cette adresse : on refuse avant même de vérifier le mot de passe (ER3-04)
        if limiteur_connexion.est_bloque(email):
            raise TooManyAttempts

        person = PersonDAO().find_by_email(email)

        # Une adresse inconnue compte aussi comme un échec : le blocage ne révèle pas si le compte existe
        if person is None or not verify_password(password, person.password):
            if limiteur_connexion.enregistrer_echec(email):
                # Une seule ligne au moment du blocage (jamais le mot de passe) : le superviseur repère les attaques
                logger.warning(f"Connexion bloquée 15 minutes après 5 échecs pour l'adresse {email.strip().lower()}")
            raise WrongCredError

        limiteur_connexion.reinitialiser(email)

        # Vérifié après le mot de passe : on n'indique pas l'état d'un compte à qui ne connaît pas son mot de passe
        if not person.active:
            raise AccountDisabled

        access_token = secrets.token_urlsafe(32)

        # Le jeton expire 24 heures après sa création
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        # Enregistre l'empreinte du jeton et sa date d'expiration
        PersonDAO().update_access_token(person.id, access_token, expires_at)

        # Le frontend reçoit le véritable jeton
        person.access_token = access_token

        return person

    def logout(self, access_token: str) -> bool:
        """Déconnecte un utilisateur en révoquant son jeton."""

        return PersonDAO().revoke_access_token(access_token)

