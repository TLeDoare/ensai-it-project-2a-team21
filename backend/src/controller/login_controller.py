from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import LoginModel, PersonModel
from service.person_service import PersonService
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_person_service():
    """Dependency provider for PersonService."""
    return PersonService()


@router.post("/", tags=["login"])
def login(credentials: LoginModel, service=Depends(get_person_service)):
    """Authenticates a user.
    Args:
        credentials: username and password.
    Returns:
        dict: containing id_player and username
    Raises:
        HTTPException: 401 error if the credentials are invalid or the user does not exist."""
    logger.info("Login")
    person = service.login(credentials.username, credentials.password)  # méthode à implémenter dans PersonService
    if person:
        return {
            "id_person": person.id_person,
            "username": person.username,
            "access_token": person.access_token,
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")
