"""Tests de OutputVerifier : lecture de la réponse du LLM et détection des omissions suspectes."""

import json

import pytest

from business_object.llm_client.output_verifier import OutputVerifier
from business_object.llm_client.prompt_templates import LLM_PII_TYPES
from utils.exceptions import LLMParseError

# Un type de PII réellement reconnu par le vérificateur, pris dans la liste officielle
TYPE_VALIDE = next(iter(LLM_PII_TYPES)).name


def reponse_llm(spans: list) -> str:
    """Fabrique une réponse JSON du LLM au format attendu : {"spans": [...]}."""
    return json.dumps({"spans": spans})


def test_json_invalide_leve_une_erreur():
    """Une réponse qui n'est pas du JSON doit lever LLMParseError."""
    with pytest.raises(LLMParseError):
        OutputVerifier().verify("ceci n'est pas du JSON", "texte")


def test_pii_trouvee_dans_le_texte():
    """Un span valide présent dans le texte donne une position, sans suspicion."""
    contenu = "Bonjour Jean Dupont, bienvenue."
    raw = reponse_llm([{"text": "Jean Dupont", "type": TYPE_VALIDE}])

    positions, suspicion = OutputVerifier().verify(raw, contenu)

    assert len(positions) == 1
    assert suspicion is False


def test_espaces_multiples_toleres():
    """Le LLM écrit « Jean Dupont » mais le texte a deux espaces : la PII est quand même retrouvée."""
    contenu = "Bonjour Jean  Dupont."
    raw = reponse_llm([{"text": "Jean Dupont", "type": TYPE_VALIDE}])

    positions, _ = OutputVerifier().verify(raw, contenu)

    assert len(positions) == 1


def test_plusieurs_occurrences_toutes_trouvees():
    """Une PII présente deux fois dans le texte donne deux positions."""
    contenu = "Jean Dupont a vu Jean Dupont."
    raw = reponse_llm([{"text": "Jean Dupont", "type": TYPE_VALIDE}])

    positions, _ = OutputVerifier().verify(raw, contenu)

    assert len(positions) == 2


@pytest.mark.parametrize(
    "span",
    [
        {"text": "Jean", "type": "TYPE_INCONNU"},  # type non autorisé
        {"text": "!!! ...", "type": TYPE_VALIDE},  # aucune lettre ni chiffre
        {"text": "", "type": TYPE_VALIDE},  # texte vide
        {"text": "Absent", "type": TYPE_VALIDE},  # texte introuvable dans le contenu
    ],
)
def test_spans_ignores(span):
    """Les spans invalides ou introuvables ne produisent aucune position."""
    positions, _ = OutputVerifier().verify(reponse_llm([span]), "Bonjour Jean !!! ...")

    assert positions == set()


def test_suspicion_si_llm_muet_mais_regex_trouvent():
    """Le LLM ne renvoie rien alors que les regex ont trouvé : suspicion d'omission ou d'attaque."""
    regex_positions = {"position_regex"}

    positions, suspicion = OutputVerifier().verify(reponse_llm([]), "texte", regex_positions)

    assert suspicion is True
    assert positions == regex_positions  # les trouvailles des regex sont gardées (fail-safe)


def test_union_llm_et_regex_sans_suspicion():
    """Quand les deux trouvent quelque chose, on garde l'union et on ne signale rien."""
    contenu = "Bonjour Jean Dupont."
    raw = reponse_llm([{"text": "Jean Dupont", "type": TYPE_VALIDE}])

    positions, suspicion = OutputVerifier().verify(raw, contenu, {"position_regex"})

    assert len(positions) == 2
    assert "position_regex" in positions
    assert suspicion is False