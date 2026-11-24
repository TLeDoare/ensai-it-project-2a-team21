"""Tests du client LLM : l'appel réseau est remplacé par un faux, on vérifie les paramètres envoyés."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from business_object.llm_client import llm_client
from business_object.llm_client.prompt_templates import SYSTEM_PROMPT


def faux_client(contenu: str) -> MagicMock:
    """Client OpenAI simulé dont la méthode create renvoie une réponse contenant `contenu`."""
    reponse = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=contenu))])
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=reponse)
    return client


@pytest.mark.asyncio
async def test_detect_pii_renvoie_la_reponse_brute(monkeypatch):
    """detect_pii renvoie le texte produit par le modèle, sans le modifier."""
    monkeypatch.setenv("LLM_MODEL", "modele-de-test")
    client = faux_client('{"spans": []}')

    with patch.object(llm_client, "create_client", return_value=client):
        resultat = await llm_client.detect_pii("Bonjour Jean Dupont.")

    assert resultat == '{"spans": []}'


@pytest.mark.asyncio
async def test_detect_pii_parametres_envoyes(monkeypatch):
    """Le modèle vient de LLM_MODEL, la sortie est en JSON, la température est basse et le prompt système est envoyé."""
    monkeypatch.setenv("LLM_MODEL", "modele-de-test")
    client = faux_client("{}")

    with patch.object(llm_client, "create_client", return_value=client):
        await llm_client.detect_pii("Bonjour Jean Dupont.")

    arguments = client.chat.completions.create.call_args.kwargs
    assert arguments["model"] == "modele-de-test"
    assert arguments["response_format"] == {"type": "json_object"}
    assert arguments["temperature"] == 0.1
    assert arguments["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    # Le document est transmis dans le message utilisateur, entre les balises de délimitation
    assert "Bonjour Jean Dupont." in arguments["messages"][1]["content"]


def test_create_client_lit_la_configuration(monkeypatch):
    """Le client est construit avec l'adresse et la clé lues dans l'environnement."""
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.exemple.fr/api")
    monkeypatch.setenv("SSPCLOUD_API_KEY", "cle-de-test")

    client = llm_client.create_client()

    assert str(client.base_url).startswith("https://llm.exemple.fr/api")
    assert client.api_key == "cle-de-test"
