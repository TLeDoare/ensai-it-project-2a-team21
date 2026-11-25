"""Tests de la matrice des droits : chaque rôle a exactement les accès prévus par grant_auth."""

from types import SimpleNamespace

import pytest

from business_object.types import Access, Role
from service.person_service import PersonService
from utils.exceptions import AuthError

U, S, A = Role.Utilisateur, Role.Superviseur, Role.Administrateur

# Tableau des droits attendus : (rôle, droit demandé, accès autorisé ?)
MATRICE = [
    # Caviarder un document : tout le monde
    (U, Access.CreateDoc, True),
    (S, Access.CreateDoc, True),
    (A, Access.CreateDoc, True),
    # Lire les documents et le journal d'audit : superviseur et administrateur
    (U, Access.ReadDoc, False),
    (S, Access.ReadDoc, True),
    (A, Access.ReadDoc, True),
    # Voir les comptes : superviseur et administrateur
    (U, Access.ReadPerson, False),
    (S, Access.ReadPerson, True),
    (A, Access.ReadPerson, True),
    # Créer un compte : administrateur seul
    (U, Access.CreatePerson, False),
    (S, Access.CreatePerson, False),
    (A, Access.CreatePerson, True),
    # Supprimer un compte : administrateur seul
    (U, Access.DeletePerson, False),
    (S, Access.DeletePerson, False),
    (A, Access.DeletePerson, True),
]


def personne(role: Role, id: int = 1):
    """Personne fictive : grant_auth n'a besoin que de son id et de son rôle."""
    return SimpleNamespace(id=id, role=role)


@pytest.mark.parametrize("role, droit, autorise", MATRICE)
def test_matrice_des_droits(role, droit, autorise):
    """Un accès prévu passe sans erreur ; un accès interdit lève AuthError."""
    if autorise:
        PersonService().grant_auth(personne(role), droit)
    else:
        with pytest.raises(AuthError):
            PersonService().grant_auth(personne(role), droit)


@pytest.mark.parametrize("role", [U, S, A])
def test_modifier_son_propre_compte_autorise(role):
    """Chacun peut modifier son propre compte, quel que soit son rôle."""
    moi = personne(role, id=7)
    PersonService().grant_auth(moi, Access.UpdatePerson, moi)


@pytest.mark.parametrize("role", [U, S, A])
def test_modifier_le_compte_d_un_autre_refuse(role):
    """Personne ne peut modifier le compte d'un autre, même l'administrateur."""
    with pytest.raises(AuthError):
        PersonService().grant_auth(personne(role, id=7), Access.UpdatePerson, personne(U, id=8))