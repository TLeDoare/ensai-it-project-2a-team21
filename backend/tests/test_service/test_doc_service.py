import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from business_object.redacted_doc import RedactedDoc
from dao.doc_dao import DocDAO
from service.doc_service import DocService


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonDAO")
@patch("service.doc_service.AnalyserFactory")
@patch("service.doc_service.MaskRedactor")
async def test_create_ok(
    mock_mask_redactor_class,
    mock_analyser_factory_class,
    mock_person_dao_class,
    mock_doc_dao_class
):
    # GIVEN
    file_content = "Ceci est un texte avec le nom Jean Dupont."
    sent_by_id = 1
    params = {"detecteur": "regex"}

    # 1. Mock de PersonDAO pour retourner un faux utilisateur avec un email
    mock_person_dao_instance = mock_person_dao_class.return_value
    mock_person_dao_instance.find_by_id = AsyncMock(return_value=AsyncMock(email="test@example.com"))

    # 2. Mock de l'analyseur (AnalyserFactory)
    mock_analyser = AsyncMock()
    mock_analyser.analyse.return_value = [{"start": 26, "end": 37, "type": "name"}]
    mock_analyser_factory_class.return_value.get_analyser.return_value = mock_analyser

    # 3. Mock du rédacteur (MaskRedactor)
    mock_redactor = mock_mask_redactor_class.return_value
    mock_redactor.redact.return_value = "Ceci est un texte avec le nom [MASQUÉ]."

    # WHEN
    result = await DocService().create(file=file_content, sent_by=sent_by_id, params=params)

    # THEN
    assert result is not None
    # Vérifie que l'auteur a bien été recherché en BDD via son ID
    mock_person_dao_instance.find_by_id.assert_called_once_with(sent_by_id)
    # Vérifie que le document caviardé a bien été enregistré via le DAO
    mock_doc_dao_class.return_value.register_document.assert_called_once()


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
async def test_find_all(mock_doc_dao_class):
    # GIVEN
    mock_doc_dao_instance = mock_doc_dao_class.return_value

    simulated_docs_list = [
        MagicMock(id=1, filename="file1.txt"),
        MagicMock(id=2, filename="file2.txt")
    ]
    mock_doc_dao_instance.find_all.return_value = simulated_docs_list

    # WHEN
    result = await DocService().find_all()

    # THEN
    assert result is not None
    assert len(result) == len(simulated_docs_list)
    assert result[0].filename == "file1.txt"
    mock_doc_dao_instance.find_all.assert_called_once()


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
async def test_find_by_id_ok(mock_doc_dao_class):
    # GIVEN
    doc_id = 1
    mock_doc_dao_instance = mock_doc_dao_class.return_value

    # On simule un faux document retourné par le DAO avec l'id donné
    fake_doc = MagicMock()
    fake_doc.id = doc_id
    fake_doc.filename = "mon_fichier.txt"
    mock_doc_dao_instance.find_by_id.return_value = fake_doc

    # WHEN
    result = await DocService().find_by_id(doc_id)

    # THEN
    assert result is not None
    assert result.id == doc_id
    assert result.filename == "mon_fichier.txt"
    mock_doc_dao_instance.find_by_id.assert_called_once_with(doc_id)


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
async def test_find_by_id_not_found(mock_doc_dao_class):
    # GIVEN
    doc_id = 999999999
    mock_doc_dao_instance = mock_doc_dao_class.return_value
    # Le DAO renvoie None si le document n'existe pas en BDD
    mock_doc_dao_instance.find_by_id.return_value = None

    # WHEN / THEN
    with pytest.raises(ValueError):
        result = await DocService().find_by_id(doc_id)
        assert result is None
