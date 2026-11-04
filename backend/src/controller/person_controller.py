from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import PersonModel, RegisterModel, UpdateModel
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
async def update_user(user: UpdateModel, person_service=Depends(get_person_service), current_person=Depends(verify_token)):
    """Update an existing user's information.
    Args:
        id_user (int)
        user (PersonModel): The new data for the user.
        person_service (PersonService): The service used to interact with user data.
    Returns:
        str: A confirmation message indicating the user was updated.
    Raises:
        HTTPException: 404 error if the user is not found.
        HTTPException: 500 error if the update process fails.
    """
    logger.info("Update a user")
    try:
        u = person_service.find_by_id(user.id)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail="User (id={id_user}) not found.") from PersonNotFound

    u.email = user.email
    u.password = user.password

    return person_service.update(u, current_person)

