"""Tests des routes /doc : chaque problème doit donner le bon code HTTP, sans lancer de vrai caviardage."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from business_object.types import Role
from controller.doc_controller import get_doc_service
from main import app
from utils.exceptions import (
    AuthError,
    DocNotFound,
    DocRegistrationError,
    LLMInjectionError,
    PseudonymisationImpossible,
    RedactorError,
)
from utils.security import verify_token


@pytest.fixture
def service():
    """Faux DocService ; create est asynchrone dans le vrai service, donc on utilise un AsyncMock."""
    faux_service = MagicMock()
    faux_service.create = AsyncMock()
    app.dependency_overrides[get_doc_service] = lambda: faux_service
    app.dependency_overrides[verify_token] = lambda: SimpleNamespace(id=1, role=Role.Utilisateur)
    yield faux_service
    app.dependency_overrides.clear()


@pytest.fixture
def client(service):
    """Client de test FastAPI, utilisé après l'installation du faux service."""
    return TestClient(app)


def televerser(client, contenu: bytes, params: str = "{}"):
    """Envoie un fichier à POST /doc/redact/, comme le fait l'interface Streamlit."""
    return client.post("/doc/redact/", files={"file": ("doc.txt", contenu)}, data={"params": params})


# --- POST /doc/redact/ : téléversement et caviardage ---

@pytest.mark.parametrize(
    "erreur, code",
    [
        (DocRegistrationError, 413),  # enregistrement en base impossible
        (RedactorError, 500),  # échec du caviardage
        (PseudonymisationImpossible("Plus de pseudonymes disponibles"), 409),  # pseudonymisation impossible
        (LLMInjectionError, 400),  # tentative d'injection détectée (F5)
    ],
)
def test_televerser_erreurs_du_service(client, service, erreur, code):
    """Chaque erreur levée par le service devient le code HTTP prévu."""
    service.create.side_effect = erreur
    assert televerser(client, b"Bonjour Jean Dupont").status_code == code


def test_televerser_fichier_non_utf8_refuse(client, service):
    """Un fichier qui n'est pas du texte UTF-8 (ici des octets invalides) est refusé en 415."""
    assert televerser(client, b"\xff\xfe\xfa").status_code == 415
    service.create.assert_not_called()


def test_televerser_fichier_trop_gros_refuse(client, service):
    """Un texte de 20 000 caractères ou plus est refusé en 413, sans appeler le service."""
    assert televerser(client, b"a" * 20000).status_code == 413
    service.create.assert_not_called()


def test_televerser_parametres_json_refuses(client, service):
    """Des paramètres écrits en JSON (true au lieu de True) sont refusés en 422."""
    assert televerser(client, b"Bonjour", params="{'pseudo': true}").status_code == 422
    service.create.assert_not_called()


# --- POST /doc/find_by_id : un document ---

@pytest.mark.parametrize("erreur, code", [(DocNotFound, 404), (AuthError, 401)])
def test_document_par_id_erreurs(client, service, erreur, code):
    """Document inconnu : 404 ; accès refusé : 401."""
    service.find_by_id.side_effect = erreur
    assert client.post("/doc/find_by_id", params={"id": 3}).status_code == code


# --- POST /doc/find_all : liste des documents ---

def test_lister_documents_ok(client, service):
    """Le service renvoie une liste vide : l'API répond 200 avec cette liste."""
    service.find_all.return_value = []
    reponse = client.post("/doc/find_all")
    assert reponse.status_code == 200
    assert reponse.json() == []


@pytest.mark.parametrize("erreur, code", [(DocNotFound, 404), (AuthError, 401)])
def test_lister_documents_erreurs(client, service, erreur, code):
    """Aucun document : 404 ; accès refusé : 401."""
    service.find_all.side_effect = erreur
    assert client.post("/doc/find_all").status_code == code