from pwdlib import PasswordHash
from fastapi import Header, HTTPException

from dao.person_dao import PersonDAO


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hache un mot de passe avant son stockage en base de données."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return password_hash.verify(password, hashed_password)


def verify_token(x_auth_token=Header(None)) -> PersonDAO:
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

    player = PersonDAO().find_by_token(x_auth_token)
    if not player:
        raise HTTPException(status_code=401, detail="Invalid token.")

    return player
