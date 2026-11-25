"""Tests de utils.security : vérification du jeton, mots de passe et empreinte HMAC des documents."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from utils.security import hash_any, hash_document, verify_password, verify_token


# --- verify_token ---

def test_verify_token_absent_refuse():
    """Sans jeton : 401 « Missing token »."""
    with pytest.raises(HTTPException) as erreur:
        verify_token(None)
    assert erreur.value.status_code == 401


@patch("utils.security.PersonDAO")
def test_verify_token_inconnu_refuse(mock_dao):
    """Jeton introuvable ou expiré en base : 401 « Invalid token »."""
    mock_dao.return_value.find_by_token.return_value = None
    with pytest.raises(HTTPException) as erreur:
        verify_token("jeton_inconnu")
    assert erreur.value.status_code == 401


@patch("utils.security.PersonDAO")
def test_verify_token_valide_renvoie_la_personne(mock_dao):
    """Jeton valide : la personne correspondante est renvoyée."""
    personne = SimpleNamespace(id=1)
    mock_dao.return_value.find_by_token.return_value = personne
    assert verify_token("bon_jeton") is personne


# --- mots de passe ---

def test_mot_de_passe_hache_puis_verifie():
    """Le bon mot de passe est accepté, un mauvais est refusé, et le hash ne contient pas le mot de passe."""
    hache = hash_any("MotDePasse1!")
    assert "MotDePasse1!" not in hache
    assert verify_password("MotDePasse1!", hache) is True
    assert verify_password("Mauvais1!", hache) is False


# --- hash_document (F4) ---

def test_hash_document_stable_et_dependant_de_la_cle(monkeypatch):
    """Même texte + même clé : même empreinte ; autre clé : autre empreinte."""
    monkeypatch.setenv("DOC_HASH_SECRET", "cle1")
    empreinte = hash_document("texte")
    assert empreinte == hash_document("texte")
    assert len(empreinte) == 64

    monkeypatch.setenv("DOC_HASH_SECRET", "cle2")
    assert hash_document("texte") != empreinte


def test_hash_document_sans_cle_refuse(monkeypatch):
    """Sans DOC_HASH_SECRET, on refuse de calculer une empreinte non protégée."""
    monkeypatch.delenv("DOC_HASH_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        hash_document("texte")