from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import LoginModel
from service.person_service import PersonService
from utils.exceptions import WrongCredError
from utils.log_utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def get_person_service():
    """Dependency provider for PersonService."""
    return PersonService()


@router.post("/")
def login(credentials: LoginModel, service=Depends(get_person_service)):
    """Authentifie un utilisateur."""

    logger.info("Login")

    try:
        person = service.login(credentials.email, credentials.password)
        return {
            "id_person": person.id,
            "email": person.email,
            "access_token": person.access_token,
        }
    except WrongCredError:
        raise HTTPException(status_code=401, detail="Invalid credentials") from WrongCredError
