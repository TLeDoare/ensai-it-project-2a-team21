"""Fonctions de validation des PII à clé de contrôle.

Le regex détecte le FORMAT ; ces fonctions vérifient la VALIDITÉ.
Elles ne servent pas à rejeter un match (on sur-caviarde), mais à
départager l'étiquette en cas de chevauchement (cf. resoudre_chevauchements).
"""

import re

from ..types import PII


def _chiffres(texte: str) -> str:
    """Ne garde que les chiffres (retire espaces + tirets + lettres)"""
    return re.sub(r"\D", "", texte)


def luhn_valide(numero: str) -> bool:
    """Validation PAN : vrai si l'algorithme de Luhn est validé"""
    chiffres = [int(c) for c in _chiffres(numero)]
    if not chiffres:
        return False
    total = 0
    for i, chiffre in enumerate(reversed(chiffres)):
        if i % 2 == 1:
            chiffre *= 2
            if chiffre > 9:
                chiffre -= 9
        total += chiffre
    return total % 10 == 0


def nir_valide(numero: str) -> bool:
    """Validation NIR : vrai si la clé de contrôle est correcte (clé = 97 - N mod 97)"""
    texte = numero.strip().upper()
    # Cas de la Corse : transformer les lettres en chiffres
    texte_num = texte.replace("2A", "19").replace("2B", "18")
    chiffres = _chiffres(texte_num)
    if len(chiffres) != 15: # 13 chiffres + 2 chiffres de clé
        return False
    corps = int(chiffres[:13])
    cle_lue = int(chiffres[13:])
    cle_attendue = 97 - (corps % 97)
    return cle_lue == cle_attendue


def iban_valide(iban: str) -> bool:
    """Validation IBAN : vrai si la validation modulo 97 (norme ISO 13616) est respectée"""
    iban = re.sub(r"\s", "", iban).upper()
    if len(iban) < 4:
        return False
    reorganise = iban[4:] + iban[:4] # déplacer les 4 premiers caractères à la fin
    # Chaque lettre = un nombre (A = 10, B = 11 etc)
    nombre = "".join(
        str(int(c, 36)) if c.isalpha() else c
        for c in reorganise
    )
    try:
        return int(nombre) % 97 == 1
    except ValueError:
        return False


VALIDATORS = {
    PII.PAN: luhn_valide,
    PII.NIR: nir_valide,
    PII.IBAN: iban_valide,
    PII.SIREN: luhn_valide,
}
