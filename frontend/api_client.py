"""Appels HTTP vers l'API Anonymia. Aucun affichage ici : app.py s'en charge."""

import os

import requests

API_URL = os.getenv("ANONYMIA_API_URL", "http://127.0.0.1:5000")
TIMEOUT = 10
TIMEOUT_LLM = 180


class ApiError(Exception):
    """Réponse d'erreur de l'API, avec le message renvoyé par le serveur."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _lire(reponse: requests.Response):
    if reponse.ok:
        return reponse.json()
    try:
        message = reponse.json().get("detail", reponse.text)
    except ValueError:
        message = reponse.text
    raise ApiError(reponse.status_code, str(message))


def api_disponible() -> bool:
    try:
        return requests.get(f"{API_URL}/openapi.json", timeout=3).ok
    except requests.RequestException:
        return False


def connexion(email: str, mot_de_passe: str) -> dict:
    reponse = requests.post(
        f"{API_URL}/login/",
        json={"email": email, "password": mot_de_passe},
        timeout=TIMEOUT,
    )
    return _lire(reponse)


def role(id_person: int, token: str) -> str:
    # La connexion ne renvoie pas le rôle. Cette route étant réservée aux superviseurs
    # et aux administrateurs, un refus signifie que la personne est un simple utilisateur.
    reponse = requests.get(
        f"{API_URL}/person/{id_person}", headers={"x-auth-token": token}, timeout=TIMEOUT
    )
    if reponse.ok:
        return reponse.json().get("role", "UTILISATEUR")
    return "UTILISATEUR"


def caviarder(token: str, nom_fichier: str, contenu: bytes, utiliser_llm: bool = True) -> dict:
    # L'API lit params avec ast.literal_eval : il faut une écriture Python (True/False), pas du JSON.
    params = repr({"llm": utiliser_llm})
    reponse = requests.post(
        f"{API_URL}/doc/redact/",
        headers={"x-auth-token": token},
        files={"file": (nom_fichier, contenu, "text/plain")},
        data={"params": params},
        timeout=TIMEOUT_LLM,
    )
    return _lire(reponse)