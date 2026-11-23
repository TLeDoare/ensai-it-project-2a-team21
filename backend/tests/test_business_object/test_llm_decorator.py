"""Tests de LLMDecorator : le vrai LLM est remplacé par un faux, on vérifie le mode dégradé et l'alerte."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from business_object.analyser.empty_analyser import EmptyAnalyser
from business_object.analyser.llm_decorator import LLMDecorator
from business_object.llm_client.prompt_templates import LLM_PII_TYPES
from business_object.types import AnalysisFail

TYPE_VALIDE = next(iter(LLM_PII_TYPES)).name
TEXTE = "Bonjour Jean Dupont."


def decorateur() -> LLMDecorator:
    """Décorateur LLM autour d'un analyseur vide ; params est requis par AnalyserDecorator mais inutilisé ici."""
    return LLMDecorator(EmptyAnalyser(), {})


def echecs(resultat: set) -> list:
    """Extrait les AnalysisFail d'un résultat d'analyse."""
    return [r for r in resultat if isinstance(r, AnalysisFail)]


@pytest.mark.asyncio
@patch("business_object.analyser.llm_decorator.detect_pii", new_callable=AsyncMock)
async def test_llm_trouve_une_pii(mock_llm):
    """Réponse valide du LLM : une position trouvée, aucune erreur."""
    mock_llm.return_value = json.dumps({"spans": [{"text": "Jean Dupont", "type": TYPE_VALIDE}]})

    resultat = await decorateur().analyse(TEXTE)

    assert len(resultat) == 1
    assert echecs(resultat) == []


@pytest.mark.asyncio
@patch("business_object.analyser.llm_decorator.detect_pii", new_callable=AsyncMock)
async def test_llm_indisponible_mode_degrade(mock_llm):
    """Le LLM plante (réseau, panne) : pas de crash, une AnalysisFail signale l'échec (mode dégradé)."""
    mock_llm.side_effect = ConnectionError("LLM injoignable")

    resultat = await decorateur().analyse(TEXTE)

    assert len(echecs(resultat)) == 1
    assert echecs(resultat)[0].source == "LLM"


@pytest.mark.asyncio
@patch("business_object.analyser.llm_decorator.OutputVerifier")
@patch("business_object.analyser.llm_decorator.detect_pii", new_callable=AsyncMock)
async def test_omission_suspecte_garde_les_pii_et_alerte(mock_llm, mock_verifier):
    """Omission suspectée : les PII trouvées sont gardées ET une alerte d'injection est ajoutée."""
    mock_llm.return_value = "{}"
    mock_verifier.return_value.verify.return_value = ({"position_trouvee"}, True)

    resultat = await decorateur().analyse(TEXTE)

    assert "position_trouvee" in resultat
    assert len(echecs(resultat)) == 1