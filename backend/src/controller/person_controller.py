from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import PersonModel, RegisterModel
from service.person_service import PersonService
from utils.exceptions import AuthError, PersonNotFound
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
        return person_service.find_all(current_person.id)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail="user (id={id_user}) not found.") from PersonNotFound
    except AuthError as a:
        raise HTTPException(status_code=401, detail=f"Accès non autorisé; vous devez être {a} au minimum.") from a

# à voir la terminologie exacte user/person


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
        return person_service.find_by_id(id_user, current_person.id)
    except PersonNotFound:
        raise HTTPException(status_code=404, detail=f"L'utilisateur d'id {id_user} est inconnu") from PersonNotFound
    except AuthError as a:
        raise HTTPException(status_code=401, detail=f"Accès non autorisé; vous devez être {a} au minimum.") from a


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
            current_person.id
        )
        if person is None:
            raise HTTPException(status_code=409, detail=f"Email {user.email} already used.")
        else:
            return person
    except AuthError as a:
        raise HTTPException(status_code=401, detail=f"Accès non autorisé; vous devez être {a} au minimum pour créer un compte.") from a


@router.put("/{id_user}", response_model=PersonModel, tags=["Users"])
async def update_user(id_user: int, user: PersonModel, person_service=Depends(get_person_service)):
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
    u = person_service.find_by_id(id_user)
    if not u:
        raise HTTPException(status_code=404, detail="User (id={id_user}) not found.")

    u.email = user.email
    u.password = user.password
    u.role = user.role

    u = person_service.update(u)
    if not u:
        raise HTTPException(status_code=500, detail="Error while updating u (user).")

    return u

