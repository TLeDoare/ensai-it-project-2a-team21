"""Tests des filtres du journal (F4) sur POST /doc/find_all : auteur et période, transmis jusqu'à la DAO."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from business_object.types import Role
from controller.doc_controller import get_doc_service
from main import app
from service.doc_service import DocService
from utils.security import verify_token


@pytest.fixture
def service():
    """Faux DocService installé à la place du vrai, avec un superviseur connecté."""
    faux_service = MagicMock()
    faux_service.find_all.return_value = []
    app.dependency_overrides[get_doc_service] = lambda: faux_service
    app.dependency_overrides[verify_token] = lambda: SimpleNamespace(id=1, role=Role.Superviseur)
    yield faux_service
    app.dependency_overrides.clear()


# --- Route ---


def test_sans_filtre_tout_le_journal(service):
    """Sans paramètre, la route se comporte comme avant : aucun filtre n'est transmis."""
    reponse = TestClient(app).post("/doc/find_all")
    assert reponse.status_code == 200
    _, auteur, debut, fin = service.find_all.call_args.args
    assert (auteur, debut, fin) == (None, None, None)


def test_filtres_transmis_au_service(service):
    """Les dates au format AAAA-MM-JJ sont converties et transmises avec l'auteur."""
    params = {"auteur": "a@a.com", "debut": "2026-11-01", "fin": "2026-11-24"}
    assert TestClient(app).post("/doc/find_all", params=params).status_code == 200
    _, auteur, debut, fin = service.find_all.call_args.args
    assert (auteur, debut, fin) == ("a@a.com", date(2026, 11, 1), date(2026, 11, 24))


def test_debut_apres_fin_refuse(service):
    """Une période à l'envers est refusée (400) sans interroger le service."""
    reponse = TestClient(app).post("/doc/find_all", params={"debut": "2026-11-24", "fin": "2026-11-01"})
    assert reponse.status_code == 400
    service.find_all.assert_not_called()


def test_date_mal_ecrite_refusee(service):
    """Une date qui n'est pas au format AAAA-MM-JJ donne une erreur de validation (422)."""
    assert TestClient(app).post("/doc/find_all", params={"debut": "24/11/2026"}).status_code == 422


# --- Service ---


@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonService")
def test_service_transmet_les_filtres_a_la_dao(mock_person_service, mock_doc_dao):
    """Le service vérifie les droits puis passe les filtres tels quels à la DAO."""
    mock_doc_dao.return_value.find_all.return_value = [MagicMock()]
    DocService().find_all("superviseur", "a@a.com", date(2026, 11, 1), None)
    mock_doc_dao.return_value.find_all.assert_called_once_with("a@a.com", date(2026, 11, 1), None)
