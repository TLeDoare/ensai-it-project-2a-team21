# Modules standards de Python
import hashlib
import hmac
import os

# Bibliothèques installées
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from pwdlib import PasswordHash

# Modules du projet
from business_object.person import Person
from dao.person_dao import PersonDAO

# Charger le .env pour disposer de DOC_HASH_SECRET
load_dotenv()


password_hash = PasswordHash.recommended()

def hash_any(any: str) -> str:
    """Hache un objet (mot de passe, un document) avant son stockage en base de données."""
    return password_hash.hash(any)

def verify_password(password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké (sel = e-mail)."""
    return password_hash.verify(password, hashed_password)


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



def hash_document(content: str) -> str:
    """Calcule l'empreinte HMAC-SHA256 d'un document (F4).

    Le même document produit toujours la même empreinte, ce qui permet de
    repérer les doublons dans le journal d'audit sans stocker le contenu.
    La clé secrète empêche de recalculer l'empreinte d'un texte deviné.

    Args:
        content: contenu brut du document.

    Returns:
        L'empreinte en hexadécimal (64 caractères).

    Raises:
        RuntimeError: si DOC_HASH_SECRET est absente du .env.
    """
    secret = os.getenv("DOC_HASH_SECRET")
    if not secret:
        # Refuser de calculer une empreinte sans clé, plutôt qu'une empreinte non protégée
        raise RuntimeError("DOC_HASH_SECRET manquante dans le .env")
    return hmac.new(secret.encode("utf-8"), content.encode("utf-8"), hashlib.sha256).hexdigest()