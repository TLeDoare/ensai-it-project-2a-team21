"""Tests du juge d'injection (FO3) dans DocService.create : verdict journalisé, caviardage jamais bloqué."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from business_object.person import Person
from business_object.types import PII, Analyser, Position
from service.doc_service import DocService

TEXTE = "Contact : noah@example.com"
POSITION = Position(indices=(10, 26), PII=PII.email, confidence=1.0, analyser_source=Analyser.Regex)
AUTEUR = Person("a@a.com", "x", "UTILISATEUR", id=1)


def caviarder(params, verdict="sain"):
    """Lance create avec un analyseur et un juge simulés ; renvoie (document, juge, DAO des injections)."""
    analyseur = MagicMock()
    analyseur.analyse = AsyncMock(return_value={POSITION})
    juge = MagicMock()
    juge.juger = AsyncMock(return_value=verdict)
    with patch("service.doc_service.AnalyserFactory") as fabrique, \
         patch("service.doc_service.InjectionJudge", return_value=juge), \
         patch("service.doc_service.InjectionAttemptDAO") as dao_injection, \
         patch("service.doc_service.PersonService"), \
         patch("service.doc_service.PersonDAO") as dao_personne, \
         patch("service.doc_service.DocDAO"), \
         patch("service.doc_service.hash_document", return_value="empreinte"):
        fabrique.return_value.get_analyser.return_value = analyseur
        dao_personne.return_value.find_by_id.return_value = MagicMock(email="a@a.com")
        doc = asyncio.run(DocService().create(TEXTE, AUTEUR, params))
    return doc, juge, dao_injection


def test_verdict_enregistre_dans_le_journal():
    doc, juge, _ = caviarder({"llm": True, "mask": True}, verdict="sain")
    juge.juger.assert_called_once_with(TEXTE)
    assert doc.params["juge_injection"] == "sain"


def test_document_suspect_caviarde_et_signale():
    """Un verdict suspect n'empêche pas le caviardage, mais la tentative est enregistrée."""
    doc, _, dao_injection = caviarder({"llm": True, "mask": True}, verdict="suspect")
    assert doc.content == "Contact : [EMAIL_1]"
    dao_injection.return_value.register_attempt.assert_called_once_with("a@a.com", "empreinte", "Juge LLM")


def test_pas_de_juge_sans_llm():
    """Sans LLM, le juge n'est pas appelé et le journal ne contient pas de verdict."""
    doc, juge, _ = caviarder({"llm": False, "mask": True})
    juge.juger.assert_not_called()
    assert "juge_injection" not in doc.params


def test_parametres_de_l_utilisateur_non_modifies():
    """Le verdict est ajouté à une copie : le dictionnaire reçu de l'utilisateur reste intact."""
    params = {"llm": True, "mask": True}
    caviarder(params)
    assert params == {"llm": True, "mask": True}
