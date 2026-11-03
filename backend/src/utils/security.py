import hashlib
from fastapi import Header, HTTPException

from dao.person_dao import PersonDAO
from business_object.person import Person


def hash_any(text: str, salt: str = "") -> str:
    password_bytes = text.encode("utf-8") + salt.encode("utf-8")
    hash_object = hashlib.sha256(password_bytes)
    return hash_object.hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return hash_any(password) == hashed_password


def verify_token(x_auth_token=Header(None)) -> Person:
    """Verifies the authenticity of a player via the provided auth token.

    This function checks if a token is present in the request headers and
    validates it against the database.
    Args:
        x_auth_token (str, optional): The token extracted from the
            'X-Auth-Token' HTTP header. Defaults to None.
    Returns:
        Player object associated with the valid token.
    Raises:
        HTTPException: 401 error if the token is missing.
        HTTPException: 401 error if the token is not found in the database.
    """
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="Missing token.")

    person = PersonDAO().find_by_token(x_auth_token)
    if person is None:
        raise HTTPException(status_code=401, detail="Invalid token.")

    return person
