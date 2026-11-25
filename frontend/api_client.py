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


def deconnexion(token: str) -> dict:
    """Révoque le jeton de l'utilisateur côté API."""

    try:
        reponse = requests.post(
            f"{API_URL}/login/logout/",
            headers={"x-auth-token": token},
            timeout=TIMEOUT,
        )
    except requests.RequestException as erreur:
        raise ApiError(
            503,
            "Impossible de contacter le serveur pour la déconnexion."
        ) from erreur

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


def caviarder(token: str, nom_fichier: str, contenu: bytes, utiliser_llm: bool = True, masquer: bool = True) -> dict:
    # L'API lit params avec ast.literal_eval : il faut une écriture Python (True/False), pas du JSON.
    params = repr({"llm": utiliser_llm, "mask": masquer})
    try:
        reponse = requests.post(
            f"{API_URL}/doc/redact/",
            headers={"x-auth-token": token},
            files={"file": (nom_fichier, contenu, "text/plain")},
            data={"params": params},
            timeout=TIMEOUT_LLM,
        )
    except requests.Timeout as erreur:
        # Message lisible au lieu d'une trace d'erreur dans l'interface
        raise ApiError(504, "Le serveur n'a pas répondu à temps. Réessayez, ou décochez le LLM.") from erreur
    return _lire(reponse)

def anonymiser_par_llm(token: str, nom_fichier: str, contenu: bytes, masquer: bool = True) -> dict:
    """FO2 : demande au LLM de réécrire lui-même le document anonymisé (rien n'est enregistré)."""
    try:
        reponse = requests.post(
            f"{API_URL}/doc/redact_llm/",
            headers={"x-auth-token": token},
            files={"file": (nom_fichier, contenu, "text/plain")},
            data={"mask": masquer},
            timeout=TIMEOUT_LLM,
        )
    except requests.Timeout as erreur:
        # Le caviardage classique reste affiché ; seule la comparaison FO2 manque
        raise ApiError(504, "Le LLM n'a pas fini de réécrire le document à temps.") from erreur
    return _lire(reponse)
    ############################################ADMIN#######

def historique(token: str) -> list:
    reponse = requests.post(f"{API_URL}/doc/find_all", headers={"x-auth-token": token}, timeout=TIMEOUT)
    # L'API répond 404 quand aucun document n'a encore été traité : ce n'est pas une erreur ici.
    if reponse.status_code == 404:
        return []
    return _lire(reponse)

def utilisateurs(token: str) -> list:
    """Renvoie la liste de tous les comptes (réservé à l'administrateur)."""
    reponse = requests.get(f"{API_URL}/person/", headers={"x-auth-token": token}, timeout=TIMEOUT)
    # Comme pour l'historique, un 404 signifie simplement qu'aucun compte n'est trouvé.
    if reponse.status_code == 404:
        return []
    return _lire(reponse)


def creer_compte(token: str, email: str, mot_de_passe: str, role_compte: str) -> dict:
    """Crée un compte avec le rôle choisi ; le mot de passe est haché par l'API."""
    reponse = requests.post(
        f"{API_URL}/person/",
        headers={"x-auth-token": token},
        json={"email": email, "password": mot_de_passe, "role": role_compte},
        timeout=TIMEOUT,
    )
    return _lire(reponse)
    
def changer_role(token: str, id_compte: int, nouveau_role: str) -> dict:
    """Change le rôle d'un compte (réservé à l'administrateur)."""
    reponse = requests.put(
        f"{API_URL}/person/{id_compte}/role",
        headers={"x-auth-token": token},
        json={"role": nouveau_role},
        timeout=TIMEOUT,
    )
    return _lire(reponse)


def changer_statut(token: str, id_compte: int, actif: bool) -> dict:
    """Désactive (actif=False) ou réactive (actif=True) un compte (réservé à l'administrateur)."""
    reponse = requests.put(
        f"{API_URL}/person/{id_compte}/active",
        headers={"x-auth-token": token},
        json={"active": actif},
        timeout=TIMEOUT,
    )
    return _lire(reponse)


def supprimer_compte(token: str, id_compte: int) -> None:
    """Supprime définitivement un compte (réservé à l'administrateur)."""
    reponse = requests.delete(
        f"{API_URL}/person/{id_compte}",
        headers={"x-auth-token": token},
        timeout=TIMEOUT,
    )
    # Une suppression réussie renvoie 204 sans contenu : il n'y a rien à lire
    if reponse.status_code == 204:
        return
    _lire(reponse)

def modifier_mon_compte(token: str, id_compte: int, email: str, mot_de_passe: str) -> dict:
    """Change le mot de passe de son propre compte ; l'API le hache et ignore l'e-mail envoyé."""
    reponse = requests.put(
        f"{API_URL}/person/{id_compte}",
        headers={"x-auth-token": token},
        # UpdateModel exige id, email et password : on renvoie l'e-mail actuel, qui ne sera pas modifié
        json={"id": id_compte, "email": email, "password": mot_de_passe},
        timeout=TIMEOUT,
    )
    return _lire(reponse)