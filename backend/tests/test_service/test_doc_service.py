import pytest
import datetime
from unittest.mock import MagicMock, patch, AsyncMock

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
