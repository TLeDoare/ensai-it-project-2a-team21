from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import ActiveModel, PersonModel, RegisterModel, RoleModel, UpdateModel
from service.person_service import PersonService
from utils.exceptions import AuthError, EmailAlreadyUsed, PersonNotFound
from utils.log_utils import get_logger
from utils.security import verify_token

router = APIRouter()

logger = get_logger(__name__)


def get_person_service():
    """Dependency provider for PersonService."""
    return PersonService()


@router.get("/", response_model=list[PersonModel], tags=["Users"])
async def find_all_users(person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """List all users.
    Returns:
        list[PlayerReadModel]: A list of all registered users.
    """
    logger.info("List all users")
    try:
        return person_service.find_all(current_person)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail="user (id={id_user}) not found.") from PersonNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError


@router.get("/{id_user}", response_model=PersonModel, tags=["Users"])
async def user_by_id(id_user: int, person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """Find a user by his unique ID.
    Args:
        id_user (int)
        person_service (PersonService): The service used to interact with person data
    Returns:
        PersonModel: The person data if found
    Raises:
        HTTPException: 404 error if the person is not found
    """
    logger.info("Find a user by id")
    try:
        return person_service.find_by_id(id_user, current_person)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError


@router.post("/", response_model=PersonModel, tags=["Users"])
def create_person(
    user: RegisterModel,
    person_service: PersonService = Depends(get_person_service),
    current_person=Depends(verify_token)
):
    logger.info("Create a user")

    try:
        person = person_service.create(
            user.email,
            user.password,
            user.role,
            current_person
        )
        return person
    except EmailAlreadyUsed:
        raise HTTPException(status_code=409, detail=f"Email {user.email} already used.") from EmailAlreadyUsed
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError


@router.put("/{id_user}", response_model=PersonModel, tags=["Users"])
async def update_user(
    id_user: int,
    user: UpdateModel,
    person_service=Depends(get_person_service),
    current_person=Depends(verify_token),
):
    """Change le mot de passe d'un compte (uniquement son propre compte).

    L'e-mail n'est pas modifiable : c'est l'identifiant de connexion et la clé du journal d'audit
    (author_email). La valeur envoyée dans le corps est donc ignorée.

    Args:
        id_user (int): identifiant du compte à modifier, lu dans l'adresse.
        user (UpdateModel): contient le nouveau mot de passe.
    Returns:
        PersonModel: le compte modifié.
    Raises:
        HTTPException: 404 si le compte n'existe pas, 403 s'il ne s'agit pas de son propre compte.
    """
    logger.info("Update a user")
    try:
        # Lecture interne (sent_by=None) : le contrôle des droits est fait par update() juste après
        u = person_service.find_by_id(id_user)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound

    # Seul le mot de passe est remplacé ; il est haché par person_service.update
    u.password = user.password

    try:
        return person_service.update(u, current_person)
    except AuthError:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que votre propre compte.") from AuthError


@router.put("/{id_user}/role", response_model=PersonModel, tags=["Users"])
def change_role(id_user: int, body: RoleModel, person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """Modifie le rôle d'un compte (administrateur uniquement)."""
    logger.info("Change the role of a user")
    try:
        return person_service.change_role(id_user, body.role, current_person)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound
    except AuthError:
        raise HTTPException(status_code=403, detail="Action non autorisée.") from AuthError


@router.put("/{id_user}/active", response_model=PersonModel, tags=["Users"])
def set_active(id_user: int, body: ActiveModel, person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """Désactive ou réactive un compte (administrateur uniquement, jamais son propre compte)."""
    logger.info("Change the status of a user")
    try:
        return person_service.set_active(id_user, body.active, current_person)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound
    except AuthError:
        raise HTTPException(status_code=403, detail="Action non autorisée.") from AuthError


@router.delete("/{id_user}", status_code=204, tags=["Users"])
def delete_user(id_user: int, person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """Supprime un compte (administrateur uniquement, jamais son propre compte)."""
    logger.info("Delete a user")
    try:
        person_service.delete(id_user, current_person)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound
    except AuthError:
        raise HTTPException(status_code=403, detail="Action non autorisée.") from AuthError