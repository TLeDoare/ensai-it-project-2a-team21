import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from business_object.llm_client import llm_client


def fausse_reponse(texte):
    message = SimpleNamespace(content=texte)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


@patch("business_object.llm_client.llm_client.create_client")
def test_detect_pii_renvoie_le_texte_du_llm(create_client_mock):
    message_mock = MagicMock()
    message_mock.choices[0].message.content = '{"spans": []}'

    create_client_mock = llm_client.create_client()
    create_client_mock.chat.completions.create = AsyncMock(return_value=message_mock)

    reponse = asyncio.run(llm_client.detect_pii("Bonjour"))

    assert reponse == '{"spans": []}'


@patch("business_object.llm_client.llm_client.create_client")
def test_detect_pii_envoie_le_document_entre_balises(create_client_mock):
    envoye = {}

    def side_effect(**kwargs):
        envoye.update(kwargs)
        res = MagicMock()
        res.choices[0].message.content = '{"spans": []}'
        return res

    create_client_mock = llm_client.create_client()
    create_client_mock.chat.completions.create = AsyncMock(side_effect=side_effect)

    asyncio.run(llm_client.detect_pii("Pierre Dupont"))

    assert "<document>\nPierre Dupont\n</document>" in envoye["messages"][1]["content"]