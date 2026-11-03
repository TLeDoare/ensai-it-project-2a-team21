from datetime import datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from business_object.types import Role
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO
from utils.exceptions import AuthError, DocNotFound
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
        print(author.role)
        if author.role == Role.Administrateur or author.role == Role.Superviseur:
            doc = DocDAO().find_by_id(id)
            if doc is None:
                raise DocNotFound
            else:
                return doc
        else:
            raise AuthError(Role.Superviseur)

    @log
    def find_all(self, sent_by: int):
        author = PersonDAO().find_by_id(sent_by)
        if author.role == Role.Administrateur or author.role == Role.Superviseur:
            docs = DocDAO().find_all()
            if docs == []:
                raise DocNotFound
            else:
                return docs
        else:
            raise AuthError(Role.Superviseur)
