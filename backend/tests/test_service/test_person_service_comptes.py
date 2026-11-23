"""Tests de PersonService : modification, changement de rôle et suppression de comptes (sans base)."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from business_object.types import Role
from service.person_service import PersonService
from utils.exceptions import AuthError, PersonNotFound

ADMIN = SimpleNamespace(id=1, role=Role.Administrateur)
SUPERVISEUR = SimpleNamespace(id=2, role=Role.Superviseur)


# --- update : modifier son propre compte ---

@patch("service.person_service.hash_any", return_value="mdp_hache")
@patch("service.person_service.PersonDAO")
def test_update_son_compte_hache_le_mot_de_passe(mock_dao, mock_hash):
    """On modifie son propre compte : le mot de passe est haché avant l'enregistrement."""
    moi = SimpleNamespace(id=5, role=Role.Utilisateur, password="NouveauMdp1!")

    PersonService().update(moi, moi)

    assert moi.password == "mdp_hache"
    mock_dao.return_value.update.assert_called_once_with(moi)


# --- change_role ---

@patch("service.person_service.PersonDAO")
def test_change_role_ok(mock_dao):
    """L'administrateur change le rôle d'un autre compte ; le mot de passe n'est pas touché (None)."""
    compte = SimpleNamespace(id=9, role=Role.Utilisateur, password="ancien_hash")
    mock_dao.return_value.find_by_id.return_value = compte

    resultat = PersonService().change_role(9, Role.Superviseur, ADMIN)

    assert resultat.role == Role.Superviseur
    assert resultat.password is None
    mock_dao.return_value.update.assert_called_once_with(compte)


@pytest.mark.parametrize("auteur, cible", [(SUPERVISEUR, 9), (ADMIN, ADMIN.id)])
def test_change_role_refuse(auteur, cible):
    """Refusé pour un non-administrateur, et pour un administrateur sur son propre compte."""
    with pytest.raises(AuthError):
        PersonService().change_role(cible, Role.Utilisateur, auteur)


@patch("service.person_service.PersonDAO")
def test_change_role_compte_inconnu(mock_dao):
    """Le compte visé n'existe pas : PersonNotFound."""
    mock_dao.return_value.find_by_id.return_value = None
    with pytest.raises(PersonNotFound):
        PersonService().change_role(99, Role.Superviseur, ADMIN)


# --- delete ---

@patch("service.person_service.PersonDAO")
def test_delete_ok(mock_dao):
    """L'administrateur supprime un autre compte existant."""
    mock_dao.return_value.delete.return_value = True
    PersonService().delete(9, ADMIN)
    mock_dao.return_value.delete.assert_called_once_with(9)


@pytest.mark.parametrize("auteur, cible", [(SUPERVISEUR, 9), (ADMIN, ADMIN.id)])
def test_delete_refuse(auteur, cible):
    """Refusé pour un non-administrateur, et pour un administrateur sur son propre compte."""
    with pytest.raises(AuthError):
        PersonService().delete(cible, auteur)


@patch("service.person_service.PersonDAO")
def test_delete_compte_inconnu(mock_dao):
    """Rien n'a été supprimé en base : PersonNotFound."""
    mock_dao.return_value.delete.return_value = False
    with pytest.raises(PersonNotFound):
        PersonService().delete(99, ADMIN)