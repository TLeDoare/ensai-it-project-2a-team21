"""Tests de InjectionAttemptDAO sur le schéma de test : journal des tentatives d'injection (F5)."""

import pytest

from dao.injection_attempt_dao import InjectionAttemptDAO


@pytest.fixture
def table_vide(connexion_test):
    """Vide la table des tentatives avant et après chaque test, pour qu'ils restent indépendants."""
    with connexion_test.cursor() as cursor:
        cursor.execute("DELETE FROM prompt_injection_attempt;")
    connexion_test.commit()

    yield

    connexion_test.rollback()  # éviter les transactions qui restent ouvertes
    with connexion_test.cursor() as cursor:
        cursor.execute("DELETE FROM prompt_injection_attempt;")
    connexion_test.commit()


def test_register_attempt_enregistre_la_tentative(table_vide):
    """Une tentative enregistrée se retrouve en base avec l'e-mail, l'empreinte et le motif."""
    InjectionAttemptDAO().register_attempt("pirate@test.fr", "empreinte123", "ignore previous instructions")

    tentatives = InjectionAttemptDAO().get_all_attempts()

    assert len(tentatives) == 1
    assert tentatives[0]["user_email"] == "pirate@test.fr"
    assert tentatives[0]["content_hash"] == "empreinte123"
    assert tentatives[0]["pattern_detected"] == "ignore previous instructions"
    assert tentatives[0]["attempt_date"] is not None


def test_get_all_attempts_plus_recente_en_premier(table_vide):
    """Les tentatives sont renvoyées de la plus récente à la plus ancienne (tableau de bord)."""
    InjectionAttemptDAO().register_attempt("a@test.fr", "h1", "motif1")
    InjectionAttemptDAO().register_attempt("b@test.fr", "h2", "motif2")

    tentatives = InjectionAttemptDAO().get_all_attempts()

    assert [t["user_email"] for t in tentatives] == ["b@test.fr", "a@test.fr"]


def test_get_all_attempts_table_vide(table_vide):
    """Sans tentative, la liste renvoyée est vide."""
    assert len(InjectionAttemptDAO().get_all_attempts()) == 0


def test_register_attempt_erreur_ne_plante_pas(table_vide):
    """Si l'enregistrement échoue (e-mail manquant, interdit en base), l'erreur est journalisée sans planter."""
    InjectionAttemptDAO().register_attempt(None, "h", "motif")

    assert len(InjectionAttemptDAO().get_all_attempts()) == 0