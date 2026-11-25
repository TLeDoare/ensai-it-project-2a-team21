"""Tests du gestionnaire d'erreur 422 de main.py : la valeur envoyée n'est jamais renvoyée (ER1-04)."""

import pytest
from fastapi.testclient import TestClient

from main import app

VALEUR_SECRETE = "valeur-secrete-a-ne-pas-renvoyer"


@pytest.fixture
def client():
    """Client de test FastAPI ; la validation échoue avant tout appel au service, aucun faux service n'est nécessaire."""
    return TestClient(app)


def test_erreur_422_sans_valeur_envoyee(client):
    """Un e-mail mal formé est refusé (422), mais la valeur envoyée n'apparaît nulle part dans la réponse."""
    reponse = client.post("/login/", json={"email": VALEUR_SECRETE, "password": "x"})

    assert reponse.status_code == 422
    assert VALEUR_SECRETE not in reponse.text


def test_erreur_422_garde_le_champ_et_le_message(client):
    """La réponse indique quel champ pose problème et pourquoi, pour que l'utilisateur puisse corriger."""
    reponse = client.post("/login/", json={"email": VALEUR_SECRETE, "password": "x"})

    erreur = reponse.json()["detail"][0]
    assert set(erreur) == {"loc", "msg", "type"}
    assert erreur["loc"] == ["body", "email"]
    assert erreur["msg"]
