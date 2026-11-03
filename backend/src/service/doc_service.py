from datetime import datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from business_object.types import Role
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO
from utils.log_utils import log
from utils.security import hash_any


class DocService:
    @log
    async def create(self, file: str, sent_by: int, params: dict) -> RedactedDoc:
        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = await analyser.analyse(text)
        doc_hash = hash_any(file)

        redactor = MaskRedactor()
        redacted_content = redactor.redact(text, positions)

        author = PersonDAO().find_by_id(sent_by)

        redacted_doc = RedactedDoc(doc_hash, datetime.now(), author.email, params, positions, None, redacted_content)
        DocDAO().register_document(redacted_doc)

        return redacted_doc

    @log
    def find_by_id(self, id: int, sent_by: id) -> RedactedDoc | None:
        author = PersonDAO().find_by_id(sent_by)
        if author.role == Role.Administrateur:
            return DocDAO().find_by_id(id)
        else:
            return None

    @log
    def find_all(self):
        return DocDAO().find_all()
