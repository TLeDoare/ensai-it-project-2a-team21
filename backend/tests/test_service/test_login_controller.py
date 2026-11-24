"""Tests des routes /login : connexion et déconnexion, avec un faux service."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from business_object.types import Role
from controller.login_controller import get_person_service
from main import app
from utils.exceptions import AccountDisabled, WrongCredError
from utils.security import verify_token

IDENTIFIANTS = {"email": "jean@test.fr", "password": "MotDePasse1!"}


@pytest.fixture
def service():
    """Faux PersonService pour /login ; attention, c'est le get_person_service de login_controller."""
    faux_service = MagicMock()
    app.dependency_overrides[get_person_service] = lambda: faux_service
    app.dependency_overrides[verify_token] = lambda: SimpleNamespace(id=1, role=Role.Utilisateur)
    yield faux_service
    app.dependency_overrides.clear()


@pytest.fixture
def client(service):
    """Client de test FastAPI, utilisé après l'installation du faux service."""
    return TestClient(app)


# --- POST /login/ : connexion ---

def test_login_ok_renvoie_le_jeton(client, service):
    """Identifiants corrects : 200, avec l'id, l'e-mail et le jeton de la personne."""
    service.login.return_value = SimpleNamespace(id=1, email="jean@test.fr", access_token="jeton123")

    reponse = client.post("/login/", json=IDENTIFIANTS)

    assert reponse.status_code == 200
    assert reponse.json() == {"id_person": 1, "email": "jean@test.fr", "access_token": "jeton123"}


def test_login_mauvais_identifiants_refuse(client, service):
    """Mauvais e-mail ou mot de passe : 401, sans jeton."""
    service.login.side_effect = WrongCredError
    assert client.post("/login/", json=IDENTIFIANTS).status_code == 401


def test_login_email_invalide_refuse(client, service):
    """Un e-mail mal formé est refusé (422) avant même d'appeler le service."""
    reponse = client.post("/login/", json={"email": "pas-un-email", "password": "x"})
    assert reponse.status_code == 422
    service.login.assert_not_called()


# --- POST /login/logout/ : déconnexion ---

def test_logout_ok(client, service):
    """Jeton valide révoqué : 200 et message de confirmation."""
    service.logout.return_value = True

    reponse = client.post("/login/logout/", headers={"x-auth-token": "jeton123"})

    assert reponse.status_code == 200
    service.logout.assert_called_once_with("jeton123")


def test_logout_jeton_invalide_refuse(client, service):
    """Le service ne trouve pas le jeton à révoquer : 401."""
    service.logout.return_value = False
    assert client.post("/login/logout/", headers={"x-auth-token": "faux"}).status_code == 401

def test_login_compte_desactive_refuse(client, service):
    """Compte désactivé : 403 avec un message explicite, sans jeton."""
    service.login.side_effect = AccountDisabled
    reponse = client.post("/login/", json=IDENTIFIANTS)
    assert reponse.status_code == 403
    assert "désactivé" in reponse.json()["detail"]
