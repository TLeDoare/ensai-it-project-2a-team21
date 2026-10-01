from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import PersonModel
from service.person_service import PersonService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_person_service():
    """Dependency provider for PersonService."""
    return PersonService()


@router.get("/", response_model=list[PersonModel], tags=["Users"])
async def find_all_users(person_service=Depends(get_person_service)):
    """List all users.
    Returns:
        list[PlayerReadModel]: A list of all registered users.
    """
    logger.info("List all users")
    users_list = person_service.find_all()
    return users_list

# à voir la terminologie exacte user/person


@router.get("/{id_user}", response_model=PersonModel, tags=["Users"])
async def user_by_id(id_user: int, person_service=Depends(get_person_service)):
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
    user = person_service.find_by_id(id_user)
    if not user:
        raise HTTPException(status_code=404, detail="user (id={id_user}) not found.")
    return user


@router.post("/", response_model=PersonModel, tags=["Users"])
async def create_player(user: PersonModel, person_service=Depends(get_person_service)):
    """Create a new user.
    Args:
        user (PersonModel): The user data to create.
        person_service (PersonService): The service used to interact with user data.
    Returns:
        PersonModel: The newly created user data.
    Raises:
        HTTPException: 400 error if the username is already taken.
        HTTPException: 500 error if the creation process fails.
    """
    logger.info("Create a user")
    if person_service.username_already_used(user.username):
        raise HTTPException(status_code=400, detail="Username already used.")

    user = person_service.create(user.email, user.password, user.role)
    if not user:
        raise HTTPException(status_code=500, detail="Error while creating user.")

    return user


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


@router.delete("/{id_user}", tags=["Users"])
async def delete_user(id_user: int, person_service=Depends(get_person_service)):
    """Delete a user from the system.
    Args:
        id_user (int)
        person_service (PersonService): The service used to interact with user data.
    Returns:
        str: A confirmation message indicating the user was deleted.
    Raises:
        HTTPException: 404 error if the user is not found.
    """
    logger.info("Delete a user")
    user = person_service.find_by_id(id_user)
    if not user:
        raise HTTPException(status_code=404, detail="User (id={id_user}) not found.")

    person_service.delete(user)
    return f"Player {user.username} deleted"
