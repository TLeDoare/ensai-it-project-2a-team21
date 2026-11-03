import asyncio
from types import SimpleNamespace

from business_object.llm_client import llm_client


def fausse_reponse(texte):
    message = SimpleNamespace(content=texte)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_detect_pii_renvoie_le_texte_du_llm(monkeypatch):
    async def faux_create(**kwargs):
        return fausse_reponse('{"spans": []}')

    monkeypatch.setattr(llm_client.client.chat.completions, "create", faux_create)

    reponse = asyncio.run(llm_client.detect_pii("Bonjour"))

    assert reponse == '{"spans": []}'


def test_detect_pii_envoie_le_document_entre_balises(monkeypatch):
    envoye = {}

    async def faux_create(**kwargs):
        envoye.update(kwargs)
        return fausse_reponse('{"spans": []}')

    monkeypatch.setattr(llm_client.client.chat.completions, "create", faux_create)

    asyncio.run(llm_client.detect_pii("Pierre Dupont"))

    assert "<document>\nPierre Dupont\n</document>" in envoye["messages"][1]["content"]