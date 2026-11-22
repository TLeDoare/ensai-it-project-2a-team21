import pytest

from business_object.analyser.validators import (
    _chiffres,
    iban_valide,
    luhn_valide,
    nir_valide,
)

# --- _chiffres ---


def test_chiffres_extrait_uniquement_les_chiffres():
    assert _chiffres("12 34-56ab78") == "12345678"
    assert _chiffres("aucun chiffre") == ""


# --- luhn_valide ---


def test_luhn_valide_cas_valide_et_avec_separateurs():
    # Exemple valide standard (49927398716) + séparation (espaces / tirets)
    assert luhn_valide("49927398716") is True
    assert luhn_valide("4992-7398-716") is True


@pytest.mark.parametrize(
    "numero",
    [
        "",  # aucun chiffre
        "abc",  # aucun chiffre après filtrage
        "49927398717",  # clé de contrôle erronée
        "79927398715",  # déclenche aussi le cas chiffre * 2 > 9
    ],
)
def test_luhn_valide_cas_invalides(numero: str):
    assert luhn_valide(numero) is False


# --- nir_valide ---


def test_nir_valide_cas_valides():
    # Pour corps = 1850578005012 -> 1850578005012 % 97 = 85 -> clé = 97 - 85 = 12
    assert nir_valide("185057800501296") is True
    assert nir_valide(" 1 85 05 78 005 012 96 ") is True


def test_nir_valide_corse_2a_et_2b():
    # Vérifie le remplacement 2A -> 19 et 2B -> 18 avant calcul de la clé
    corps_2a = int("1190578005012")
    cle_2a = 97 - (corps_2a % 97)
    nir_2a = f"12A0578005012{cle_2a:02d}"
    assert nir_valide(nir_2a) is True

    corps_2b = int("1180578005012")
    cle_2b = 97 - (corps_2b % 97)
    nir_2b = f"12B0578005012{cle_2b:02d}"
    assert nir_valide(nir_2b) is True


@pytest.mark.parametrize(
    "numero",
    [
        "12345",  # longueur != 15
        "185057800501299",  # mauvaise clé de contrôle
    ],
)
def test_nir_valide_cas_invalides(numero: str):
    assert nir_valide(numero) is False


# --- iban_valide ---


def test_iban_valide_cas_valide():
    # FR76 3000 6000 0112 3456 7890 189 est un IBAN FR valide (modulo 97 == 1)
    assert iban_valide("FR76 3000 6000 0112 3456 7890 189") is True
    assert iban_valide("fr7630006000011234567890189") is True


@pytest.mark.parametrize(
    "iban",
    [
        "",  # trop court (< 4)
        "FR7",  # trop court (< 4)
        "FR76 3000 6000 0112 3456 7890 180",  # clé / contrôle invalide
        "FR76-3000-6000-0112",  # caractères non alphanumériques ('-') -> ValueError
    ],
)
def test_iban_valide_cas_invalides(iban: str):
    assert iban_valide(iban) is False
