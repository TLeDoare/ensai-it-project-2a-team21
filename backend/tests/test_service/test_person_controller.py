"""Tests des routes /person : chaque erreur du service doit devenir le bon code HTTP."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from business_object.types import Role
from controller.person_controller import get_person_service
from main import app
from utils.exceptions import AuthError, EmailAlreadyUsed, PersonNotFound
from utils.security import verify_token


@pytest.fixture
def service():
    """Faux PersonService, injecté à la place du vrai ; on choisit ce qu'il renvoie ou lève."""
    faux_service = MagicMock()
    app.dependency_overrides[get_person_service] = lambda: faux_service
    app.dependency_overrides[verify_token] = lambda: SimpleNamespace(id=1, role=Role.Administrateur)
    yield faux_service
    app.dependency_overrides.clear()


@pytest.fixture
def client(service):
    """Client de test FastAPI, utilisé après l'installation du faux service."""
    return TestClient(app)


# --- GET /person/ : liste des comptes ---

def test_lister_comptes_ok(client, service):
    """Le service renvoie une liste vide : l'API répond 200 avec cette liste."""
    service.find_all.return_value = []
    reponse = client.get("/person/")
    assert reponse.status_code == 200
    assert reponse.json() == []


def test_lister_comptes_non_autorise(client, service):
    """Le service refuse l'accès : l'API répond 401."""
    service.find_all.side_effect = AuthError
    assert client.get("/person/").status_code == 401


def test_lister_comptes_introuvable(client, service):
    """Le service ne trouve rien : l'API répond 404."""
    service.find_all.side_effect = PersonNotFound
    assert client.get("/person/").status_code == 404


# --- GET /person/{id} : un compte ---

@pytest.mark.parametrize("erreur, code", [(PersonNotFound, 404), (AuthError, 401)])
def test_compte_par_id_erreurs(client, service, erreur, code):
    """Compte inconnu : 404 ; accès refusé : 401."""
    service.find_by_id.side_effect = erreur
    assert client.get("/person/5").status_code == code


# --- POST /person/ : création ---

# Mot de passe fort : majuscule, minuscule, chiffre, caractère spécial, 8 caractères ou plus (PASSWORD_REGEX)
NOUVEAU_COMPTE = {"email": "nouveau@test.fr", "password": "MotDePasse1!", "role": "UTILISATEUR"}


@pytest.mark.parametrize("erreur, code", [(EmailAlreadyUsed, 409), (AuthError, 401)])
def test_creer_compte_erreurs(client, service, erreur, code):
    """E-mail déjà pris : 409 ; créateur non autorisé : 401."""
    service.create.side_effect = erreur
    assert client.post("/person/", json=NOUVEAU_COMPTE).status_code == code


def test_creer_compte_mot_de_passe_faible_refuse(client, service):
    """Un mot de passe trop faible est refusé (422) avant même d'atteindre le service."""
    compte_faible = {**NOUVEAU_COMPTE, "password": "motdepasse"}
    assert client.post("/person/", json=compte_faible).status_code == 422
    service.create.assert_not_called()


# --- PUT /person/{id} : modification ---

def test_modifier_compte_introuvable(client, service):
    """Le compte à modifier n'existe pas : 404."""
    service.find_by_id.side_effect = PersonNotFound
    corps = {"id": 5, "email": "x@test.fr", "password": "NouveauMdp1!"}
    assert client.put("/person/5", json=corps).status_code == 404


# --- PUT /person/{id}/role : changement de rôle ---

@pytest.mark.parametrize("erreur, code", [(PersonNotFound, 404), (AuthError, 403)])
def test_changer_role_erreurs(client, service, erreur, code):
    """Compte inconnu : 404 ; non-administrateur : 403."""
    service.change_role.side_effect = erreur
    assert client.put("/person/5/role", json={"role": "SUPERVISEUR"}).status_code == code


# --- DELETE /person/{id} : suppression ---

def test_supprimer_compte_ok(client, service):
    """Suppression réussie : 204, et le service a bien été appelé pour ce compte."""
    reponse = client.delete("/person/5")
    assert reponse.status_code == 204
    service.delete.assert_called_once()


@pytest.mark.parametrize("erreur, code", [(PersonNotFound, 404), (AuthError, 403)])
def test_supprimer_compte_erreurs(client, service, erreur, code):
    """Compte inconnu : 404 ; non-administrateur ou son propre compte : 403."""
    service.delete.side_effect = erreur
    assert client.delete("/person/5").status_code == code

# --- PUT /person/{id}/active : désactivation et réactivation (F1) ---

def test_desactiver_compte_ok(client, service):
    """Désactivation réussie : 200, le compte renvoyé est inactif, et le service a reçu le bon statut."""
    service.set_active.return_value = SimpleNamespace(id=5, email="x@test.fr", role=Role.Utilisateur, active=False)

    reponse = client.put("/person/5/active", json={"active": False})

    assert reponse.status_code == 200
    assert reponse.json()["active"] is False
    assert service.set_active.call_args.args[:2] == (5, False)


@pytest.mark.parametrize("erreur, code", [(PersonNotFound, 404), (AuthError, 403)])
def test_desactiver_compte_erreurs(client, service, erreur, code):
    """Compte inconnu : 404 ; non-administrateur ou son propre compte : 403."""
    service.set_active.side_effect = erreur
    assert client.put("/person/5/active", json={"active": False}).status_code == code
