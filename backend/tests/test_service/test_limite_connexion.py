"""Tests de la limite d'essais de connexion (constat d'audit ER3-04) : limiteur, service et route."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from controller.login_controller import get_person_service
from main import app
from service.person_service import PersonService
from utils.exceptions import TooManyAttempts, WrongCredError
from utils.limiteur_connexion import LimiteurConnexion, limiteur_connexion


class FausseHorloge:
    """Horloge réglable à la main, pour simuler le temps qui passe sans attendre."""

    def __init__(self):
        self.maintenant = 1000.0

    def __call__(self):
        return self.maintenant


@pytest.fixture
def horloge():
    return FausseHorloge()


@pytest.fixture
def limiteur(horloge):
    return LimiteurConnexion(horloge)


# --- Limiteur ---


def test_bloque_au_cinquieme_echec(limiteur):
    for _ in range(4):
        assert limiteur.enregistrer_echec("a@a.com") is False
    assert not limiteur.est_bloque("a@a.com")
    # Seul l'échec qui déclenche le blocage renvoie True
    assert limiteur.enregistrer_echec("a@a.com") is True
    assert limiteur.est_bloque("a@a.com")


def test_deblocage_apres_quinze_minutes(limiteur, horloge):
    for _ in range(5):
        limiteur.enregistrer_echec("a@a.com")
    horloge.maintenant += 15 * 60
    assert not limiteur.est_bloque("a@a.com")


def test_echecs_anciens_oublies(limiteur, horloge):
    """Des échecs espacés de plus de 15 minutes ne s'additionnent pas."""
    for _ in range(4):
        limiteur.enregistrer_echec("a@a.com")
    horloge.maintenant += 16 * 60
    limiteur.enregistrer_echec("a@a.com")
    assert not limiteur.est_bloque("a@a.com")


def test_majuscules_et_espaces_ignores(limiteur):
    for _ in range(5):
        limiteur.enregistrer_echec(" A@A.com")
    assert limiteur.est_bloque("a@a.com")


def test_autres_adresses_non_bloquees(limiteur):
    for _ in range(5):
        limiteur.enregistrer_echec("a@a.com")
    assert not limiteur.est_bloque("b@b.com")


def test_reinitialiser_efface_les_echecs(limiteur):
    for _ in range(4):
        limiteur.enregistrer_echec("a@a.com")
    limiteur.reinitialiser("a@a.com")
    limiteur.enregistrer_echec("a@a.com")
    assert not limiteur.est_bloque("a@a.com")


# --- Service ---


@pytest.fixture
def limiteur_vide():
    """Remet à zéro le limiteur partagé avant et après le test, pour ne pas gêner les autres tests."""
    limiteur_connexion.echecs.clear()
    limiteur_connexion.bloque_jusqu_a.clear()
    yield limiteur_connexion
    limiteur_connexion.echecs.clear()
    limiteur_connexion.bloque_jusqu_a.clear()


@patch("service.person_service.verify_password", return_value=False)
@patch("service.person_service.PersonDAO")
def test_service_bloque_meme_avec_le_bon_mot_de_passe(mock_dao, mock_verify, limiteur_vide):
    """Après 5 échecs, même le bon mot de passe est refusé, sans être vérifié."""
    mock_dao.return_value.find_by_email.return_value = MagicMock(active=True)
    for _ in range(5):
        with pytest.raises(WrongCredError):
            PersonService().login("x@test.fr", "Faux1!")

    mock_verify.return_value = True
    mock_verify.reset_mock()
    with pytest.raises(TooManyAttempts):
        PersonService().login("x@test.fr", "MotDePasse1!")
    mock_verify.assert_not_called()


@patch("service.person_service.logger")
@patch("service.person_service.PersonDAO")
def test_service_blocage_ecrit_une_ligne_de_log(mock_dao, mock_logger, limiteur_vide):
    """Le blocage est signalé une seule fois dans le log, avec l'adresse mais jamais le mot de passe."""
    mock_dao.return_value.find_by_email.return_value = None
    for _ in range(5):
        with pytest.raises(WrongCredError):
            PersonService().login("X@test.fr", "Secret1!")
    mock_logger.warning.assert_called_once()
    message = mock_logger.warning.call_args.args[0]
    assert "x@test.fr" in message
    assert "Secret1!" not in message


@patch("service.person_service.PersonDAO")
def test_service_adresse_inconnue_compte_aussi(mock_dao, limiteur_vide):
    """Une adresse inexistante est bloquée comme une autre : le blocage ne révèle pas si le compte existe."""
    mock_dao.return_value.find_by_email.return_value = None
    for _ in range(5):
        with pytest.raises(WrongCredError):
            PersonService().login("inconnu@test.fr", "Faux1!")
    assert limiteur_vide.est_bloque("inconnu@test.fr")


@patch("service.person_service.verify_password", return_value=True)
@patch("service.person_service.PersonDAO")
def test_service_reussite_remet_a_zero(mock_dao, mock_verify, limiteur_vide):
    """Une connexion réussie efface les échecs précédents."""
    mock_dao.return_value.find_by_email.return_value = MagicMock(id=1, active=True)
    for _ in range(4):
        limiteur_vide.enregistrer_echec("x@test.fr")
    PersonService().login("x@test.fr", "MotDePasse1!")
    assert limiteur_vide.echecs.get("x@test.fr") is None


# --- Route POST /login/ ---


def test_route_renvoie_429():
    faux_service = MagicMock()
    faux_service.login.side_effect = TooManyAttempts
    app.dependency_overrides[get_person_service] = lambda: faux_service
    try:
        reponse = TestClient(app).post("/login/", json={"email": "a@a.com", "password": "x"})
    finally:
        app.dependency_overrides.clear()
    assert reponse.status_code == 429
    assert "15 minutes" in reponse.json()["detail"]
