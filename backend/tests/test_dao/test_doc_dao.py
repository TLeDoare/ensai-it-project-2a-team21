from datetime import datetime

import pytest

from business_object.redacted_doc import RedactedDoc
from business_object.types import Analyser, PII, Position
from dao.doc_dao import DocDAO, DocRegistrationError


@pytest.fixture
def id_person_test(connexion_test):
    """Crée un utilisateur provisoire et renvoie son id, puis nettoie 
    les trois tables après"""
    with connexion_test.cursor() as cursor:
        cursor.execute(
            "INSERT INTO person (email, password, role) "
            "VALUES (%s, %s, %s) RETURNING id;",
            ("test@test.fr", "motdepasse", "utilisateur"),
        )
        id_person = cursor.fetchone()["id"]
    connexion_test.commit()

    yield id_person

    connexion_test.rollback()     # éfviter les transactions qui restent ouvertes
    with connexion_test.cursor() as cursor:
        cursor.execute("DELETE FROM traitement;")
        cursor.execute("DELETE FROM redacteddoc;")
        cursor.execute("DELETE FROM person;")
    connexion_test.commit()


def _doc_factice(id_person: int, nb_pii: int = 2) -> RedactedDoc:
    """Construit un RedactedDoc de test avec nb_pii positions détectées"""
    details = {
        Position(indices=(i, i + 5), PII=PII.last_name,
                 confidence=0.9, analyser_source=Analyser.Regex)
        for i in range(0, nb_pii * 10, 10)
    }
    return RedactedDoc(
        filename="test.txt",
        upload_date=datetime.now(),
        sent_by=id_person,
        params={"strategie": "masquage"},
        details=details,
    )


def test_register_document_cree_doc_et_lien(connexion_test, id_person_test):
    doc = _doc_factice(id_person_test, nb_pii=2)

    ok = DocDAO().register_document(doc, id_person_test)

    assert ok is True
    assert doc.id is not None

    with connexion_test.cursor() as cursor:
        cursor.execute(
            "SELECT filename, pii_count FROM redacteddoc WHERE id = %s;",
            (doc.id,),
        )
        ligne = cursor.fetchone()
    assert ligne is not None
    assert ligne["filename"] == "test.txt"
    assert ligne["pii_count"] == 2

    with connexion_test.cursor() as cursor:
        cursor.execute(
            "SELECT id_person FROM traitement WHERE id_doc = %s;",
            (doc.id,),
        )
        lien = cursor.fetchone()
    assert lien is not None
    assert lien["id_person"] == id_person_test


def test_register_document_sans_pii(connexion_test, id_person_test):
    """Un document sans PII s'enregistre avec un compte de 0 PII"""
    doc = _doc_factice(id_person_test, nb_pii=0)

    ok = DocDAO().register_document(doc, id_person_test)

    assert ok is True
    with connexion_test.cursor() as cursor:
        cursor.execute(
            "SELECT pii_count FROM redacteddoc WHERE id = %s;", (doc.id,)
        )
        ligne = cursor.fetchone()
    assert ligne["pii_count"] == 0


def test_register_document_personne_inexistante(connexion_test, id_person_test):
    """Un document avec l'id d'une personne inexistante renvoie une erreur"""
    doc = _doc_factice(id_person_test, nb_pii=1)
    id_inexistant = 999_999

    with pytest.raises(DocRegistrationError):
        DocDAO().register_document(doc, id_inexistant)

    connexion_test.rollback()
    with connexion_test.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS n FROM redacteddoc;")
        n = cursor.fetchone()["n"]
    assert n == 0