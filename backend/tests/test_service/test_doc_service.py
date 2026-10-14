from unittest.mock import MagicMock

from business_object.redacted_doc import RedactedDoc
from dao.doc_dao import DocDAO
from service.doc_service import DocService
import datetime


list_docs = [
    RedactedDoc(filename="fichier1", upload_date=datetime.datetime(2026, 10, 14, 19, 39, 50), sent_by=Person1, params={"detecteur": regex}, details=["Position", ["indices", "PII", "confidence", "analyser_source"]], hash="contenu haché_1"),
    RedactedDoc(filename="fichier1", upload_date=datetime.datetime(2027, 8, 25, 19, 46, 10), sent_by=Person2, params={"detecteur": llm}, details=["Position", ["indices", "PII", "confidence", "analyser_source"]], hash="contenu haché_2")

]

def test_create_ok():
    """Vérifie la création d'un document"""
    # GIVEN
    filename, upload_date, sent_by, params, details, hash = "file", datetime.datetime(2020, 2, 3, 5, 39, 50), User, {}, [], "hash"
    DocDAO().register_document = MagicMock(return_value=True)

    # WHEN
    doc1 = DocService().create(filename, upload_date, sent_by, params, details, hash)

    # THEN
    assert doc1.filename == filename
