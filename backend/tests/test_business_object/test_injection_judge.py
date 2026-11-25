"""Tests du juge d'injection (FO3) : le LLM est simulé, on vérifie la lecture de son verdict."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from business_object.llm_client import injection_judge, llm_client
from business_object.llm_client.injection_judge import INDISPONIBLE, SAIN, SUSPECT, InjectionJudge
from business_object.llm_client.prompt_templates import JUDGE_SYSTEM_PROMPT


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reponse_llm, verdict",
    [
        ('{"injection": true}', SUSPECT),
        ('{"injection": false}', SAIN),
        ("pas du JSON", INDISPONIBLE),  # réponse illisible
        ('{"injection": "peut-être"}', INDISPONIBLE),  # valeur inattendue
        ("[]", INDISPONIBLE),  # JSON qui n'est pas un objet
    ],
)
async def test_lecture_du_verdict(reponse_llm, verdict):
    with patch.object(injection_judge, "juger_injection", AsyncMock(return_value=reponse_llm)):
        assert await InjectionJudge().juger("Bonjour.") == verdict


@pytest.mark.asyncio
async def test_llm_injoignable_donne_indisponible():
    """Une panne du LLM ne remonte pas : le juge répond INDISPONIBLE."""
    with patch.object(injection_judge, "juger_injection", AsyncMock(side_effect=TimeoutError)):
        assert await InjectionJudge().juger("Bonjour.") == INDISPONIBLE


@pytest.mark.asyncio
async def test_parametres_envoyes_au_llm():
    """Prompt du juge, sortie JSON imposée, température nulle et réponse courte."""
    reponse = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"injection": false}'))])
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=reponse)

    with patch.object(llm_client, "create_client", return_value=client):
        await llm_client.juger_injection("Bonjour Jean Martin.")

    arguments = client.chat.completions.create.call_args.kwargs
    assert arguments["messages"][0] == {"role": "system", "content": JUDGE_SYSTEM_PROMPT}
    assert "Bonjour Jean Martin." in arguments["messages"][1]["content"]
    assert arguments["response_format"] == {"type": "json_object"}
    assert arguments["temperature"] == 0.0
