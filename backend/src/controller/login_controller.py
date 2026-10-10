from fastapi import APIRouter, Depends, HTTPException

from schema.person_model import LoginModel
from service.person_service import PersonService
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

    person = service.login(credentials.email, credentials.password)

    if person:
        return {
            "id_person": person.id,
            "email": person.email,
            "access_token": person.access_token,
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")
