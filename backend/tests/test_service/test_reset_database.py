"""Tests de la route GET /reset_database : seul un administrateur peut vider la base."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from business_object.types import Role
from main import app
from utils.security import verify_token


@pytest.fixture
def client():
    """Client de test FastAPI ; les remplacements de dépendances sont effacés après chaque test."""
    yield TestClient(app)
    app.dependency_overrides.clear()


def connecter_en_tant_que(role: Role):
    """Remplace verify_token pour simuler une personne connectée avec le rôle donné."""
    app.dependency_overrides[verify_token] = lambda: SimpleNamespace(role=role)


def test_reset_database_sans_jeton_refuse(client):
    """Sans jeton, l'API répond 401 avant même d'entrer dans la route."""
    reponse = client.get("/reset_database")
    assert reponse.status_code == 401


@pytest.mark.parametrize("role", [Role.Utilisateur, Role.Superviseur])
@patch("main.ResetDatabase")
def test_reset_database_non_admin_refuse(mock_reset, client, role):
    """Un utilisateur ou un superviseur connecté reçoit 403, et la base n'est pas touchée."""
    connecter_en_tant_que(role)
    reponse = client.get("/reset_database")
    assert reponse.status_code == 403
    mock_reset.return_value.run.assert_not_called()


@patch("main.ResetDatabase")
def test_reset_database_admin_autorise(mock_reset, client):
    """Un administrateur obtient 200 ; la réinitialisation est simulée par un mock."""
    mock_reset.return_value.run.return_value = True
    connecter_en_tant_que(Role.Administrateur)
    reponse = client.get("/reset_database")
    assert reponse.status_code == 200
    assert "SUCCESS" in reponse.json()["message"]
    mock_reset.return_value.run.assert_called_once()