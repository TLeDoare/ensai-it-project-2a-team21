"""Tests des filtres du journal (F4) dans DocDAO.find_all, sur le schéma de test."""

from datetime import date, datetime

import pytest

from business_object.redacted_doc import RedactedDoc
from dao.doc_dao import DocDAO


@pytest.fixture
def journal(connexion_test):
    """Enregistre trois traitements (deux auteurs, trois dates), puis vide la table après le test."""
    for auteur, jour in [("a@a.com", 1), ("b@b.com", 10), ("a@a.com", 20)]:
        DocDAO().register_document(
            RedactedDoc(hash=f"doc{jour}", upload_date=datetime(2026, 11, jour, 15, 30), sent_by=auteur,
                        params={"llm": False}, details=set())
        )
    yield
    connexion_test.rollback()
    with connexion_test.cursor() as cursor:
        cursor.execute("DELETE FROM redacteddoc;")
    connexion_test.commit()


def test_sans_filtre_tout_du_plus_recent_au_plus_ancien(journal):
    assert [d.hash for d in DocDAO().find_all()] == ["doc20", "doc10", "doc1"]


def test_filtre_auteur_sans_tenir_compte_des_majuscules(journal):
    assert [d.hash for d in DocDAO().find_all(auteur=" A@A.com ")] == ["doc20", "doc1"]


def test_filtre_periode_dates_incluses(journal):
    """Le 10 et le 20 novembre sont inclus, même si les traitements ont eu lieu l'après-midi."""
    documents = DocDAO().find_all(debut=date(2026, 11, 10), fin=date(2026, 11, 20))
    assert [d.hash for d in documents] == ["doc20", "doc10"]


def test_filtres_combines(journal):
    assert [d.hash for d in DocDAO().find_all(auteur="a@a.com", fin=date(2026, 11, 15))] == ["doc1"]
