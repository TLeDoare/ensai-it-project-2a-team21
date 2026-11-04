from datetime import datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.analyser.overlap import resoudre_chevauchements
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from business_object.redactor.pseudonimise_redactor import PseudonimiseRedactor
from business_object.redactor.redactorcontext import RedactorContext
from business_object.types import Access
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO
from service.person_service import PersonService
from utils.exceptions import DocNotFound
from utils.log_utils import log
from utils.security import hash_any


class DocService:
    @log
    async def create(self, file: str, sent_by: int, params: dict) -> RedactedDoc:
        PersonService().grant_auth(sent_by, Access.CreateDoc)

        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = await analyser.analyse(text)
        positions = resoudre_chevauchements(positions, text)
        doc_hash = hash_any(file)

        redactor_context = RedactorContext()
        if params.get("mask", True):
            redactor_context.set_strategy(MaskRedactor())
        else:
            redactor_context.set_strategy(PseudonimiseRedactor())

        redacted_content = redactor_context.execute_strategy(file, positions)

        author = PersonDAO().find_by_id(sent_by)

        redacted_doc = RedactedDoc(doc_hash, datetime.now(), author.email, params, positions, None, redacted_content)
        DocDAO().register_document(redacted_doc)

        return redacted_doc

    @log
    def find_by_id(self, id: int, sent_by: id) -> RedactedDoc:
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        doc = DocDAO().find_by_id(id)
        if doc is None:
            raise DocNotFound
        else:
            return doc

    @log
    def find_all(self, sent_by: int):
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        docs = DocDAO().find_all()
        if docs == []:
            raise DocNotFound
        else:
            return docs
