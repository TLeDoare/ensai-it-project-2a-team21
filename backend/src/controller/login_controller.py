from fastapi import APIRouter, Depends, Header, HTTPException

from schema.person_model import LoginModel
from service.person_service import PersonService
from utils.exceptions import WrongCredError
from utils.log_utils import get_logger
from utils.security import verify_token

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


@router.post("/logout/")
def logout(
    x_auth_token: str = Header(...),
    service: PersonService = Depends(get_person_service),
    current_person=Depends(verify_token),
):
    """Déconnecte l'utilisateur en révoquant son jeton."""

    success = service.logout(x_auth_token)

    if not success:
        raise HTTPException(
            status_code=401,
            detail="Jeton invalide."
        )

    return {"message": "Déconnexion réussie."}
