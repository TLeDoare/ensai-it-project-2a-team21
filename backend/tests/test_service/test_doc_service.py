from unittest.mock import MagicMock, patch

import pytest

from business_object.person import Person
from business_object.types import PII, Access, Analyser, Position
from service.doc_service import DocService
from utils.exceptions import DocNotFound


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonService")
async def test_find_all(mock_person_service, mock_doc_dao_class):
    # GIVEN
    mock_doc_dao_instance = mock_doc_dao_class.return_value

    mock_person_service_instance = mock_person_service.return_value
    mock_person_service_instance.grant_auth = MagicMock(return_value=None)

    simulated_docs_list = [
        MagicMock(id=1, filename="file1.txt"),
        MagicMock(id=2, filename="file2.txt")
    ]
    mock_doc_dao_instance.find_all = MagicMock(return_value = simulated_docs_list)

    # WHEN
    result = DocService().find_all(12)

    # THEN
    assert result is not None
    assert len(result) == len(simulated_docs_list)
    assert result[0].filename == "file1.txt"
    mock_person_service_instance.grant_auth.assert_called_once_with(12, Access.ReadDoc)
    mock_doc_dao_instance.find_all.assert_called_once()


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonService")
async def test_find_by_id_ok(mock_person_service, mock_doc_dao_class):
    # GIVEN
    doc_id = 1
    mock_doc_dao_instance = mock_doc_dao_class.return_value

    # On simule un faux document retourné par le DAO avec l'id donné
    fake_doc = MagicMock()
    fake_doc.id = doc_id
    fake_doc.filename = "mon_fichier.txt"
    mock_doc_dao_instance.find_by_id.return_value = fake_doc

    mock_person_service_instance = mock_person_service.return_value
    mock_person_service_instance.grant_auth = MagicMock(return_value=None)

    # WHEN
    result = DocService().find_by_id(doc_id, 15)

    # THEN
    assert result is not None
    assert result.id == doc_id
    assert result.filename == "mon_fichier.txt"
    mock_doc_dao_instance.find_by_id.assert_called_once_with(doc_id)
    mock_person_service_instance.grant_auth.assert_called_once_with(15, Access.ReadDoc)


@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonService")
async def test_find_by_id_not_found(mock_person_service, mock_doc_dao_class):
    # GIVEN
    doc_id = 999999999
    mock_doc_dao_instance = mock_doc_dao_class.return_value
    # Le DAO renvoie None si le document n'existe pas en BDD
    mock_doc_dao_instance.find_by_id.return_value = None

    mock_person_service_instance = mock_person_service.return_value
    mock_person_service_instance.grant_auth = MagicMock(return_value=None)

    # WHEN / THEN
    with pytest.raises(DocNotFound):
        result = DocService().find_by_id(doc_id, 13)
        assert result is None

@pytest.mark.asyncio
@patch("service.doc_service.hash_any", return_value="hash_test")
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonDAO")
@patch("business_object.redacted_doc.RedactedDoc")
@patch("service.doc_service.PersonService")
async def test_create_avec_vrai_mask_redactor(
    mock_person_service,
    mock_redacted_doc_class,
    mock_person_dao_class,
    mock_doc_dao_class,
    mock_hash
):
    # GIVEN
    content = "Contact : noah@example.com"
    sent_by = Person("test@a.com", "####", "UTILISATEUR")
    params = {'llm': False}

    positions = {
        Position(
            indices=(10, 26),
            PII=PII.email,
            confidence=1.0,
            analyser_source=Analyser.Regex
        )
    }

    mock_person_service_instance = mock_person_service.return_value
    mock_person_service_instance.grant_auth = MagicMock(return_value=None)

    # Simuler la récupération de l'auteur
    mock_person_dao_class.return_value.find_by_id.return_value = (
        MagicMock(email="test@example.com")
    )

    # WHEN
    result = await DocService().create(
        file=content,
        sent_by=sent_by,
        params=params
    )

    # THEN
    # Vérifier le texte transmis à RedactedDoc
    assert result.content == "Contact : [EMAIL_1]"
    assert result.details == positions

    # Vérifier que le document est transmis au DAO
    mock_doc_dao_class.return_value.register_document.assert_called_once_with(
        result
    )

    mock_person_service_instance.grant_auth.assert_called_once_with(sent_by, Access.CreateDoc)

    mock_hash.assert_called_once_with(content)


@pytest.mark.llm
@pytest.mark.asyncio
@patch("service.doc_service.DocDAO")
@patch("service.doc_service.PersonDAO")
@patch("service.doc_service.PersonService")
async def test_create_ok(
    mock_person_service,
    mock_person_dao_class,
    mock_doc_dao_class
):
    # GIVEN
    file_content = "Ceci est un texte avec le nom Jean Dupont."
    sent_by = Person("test@a.com", "####", "UTILISATEUR")
    params = {'llm': True}

    # 1. Mock de PersonDAO pour retourner un faux utilisateur avec un email
    mock_person_instance = Person("test@nexistepas.com", "####", "UTILISATEUR", id=12)

    mock_person_dao_instance = mock_person_dao_class.return_value
    mock_person_dao_instance.find_by_id = MagicMock(return_value=mock_person_instance)

    mock_person_service_instance = mock_person_service.return_value
    mock_person_service_instance.grant_auth = MagicMock(return_value=None)

    # WHEN
    result = await DocService().create(file=file_content, sent_by=sent_by, params=params)

    # THEN
    assert result is not None
    # Vérifie que l'auteur a bien été recherché en BDD via son ID
    mock_person_service_instance.grant_auth.assert_called_once_with(sent_by, Access.CreateDoc)
    # Vérifie que le document caviardé a bien été enregistré via le DAO
    mock_doc_dao_class.return_value.register_document.assert_called_once()
