from datetime import datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.analyser.overlap import resoudre_chevauchements
from business_object.person import Person
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from business_object.redactor.pseudonimise_redactor import PseudonimiseRedactor
from business_object.redactor.pseudonymes import PSEUDO_VALUES
from business_object.redactor.redactorcontext import RedactorContext
from business_object.types import Access, AnalysisFail
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO
from service.person_service import PersonService
from utils.exceptions import DocNotFound
from utils.log_utils import get_logger, log
from utils.security import hash_any

logger = get_logger(__name__)


class DocService:
    async def create(self, file: str, sent_by: Person, params: dict) -> RedactedDoc:
        logger.info(f"{sent_by.email} caviarde un document avec les paramètres {params}")
        PersonService().grant_auth(sent_by, Access.CreateDoc)

        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = await analyser.analyse(text)

        # On s'assure ici que l'analyse n'a pas rencontré de problème
        analysis_fail = None
        positions_filtrees = set()
        for pos in positions:
            if isinstance(pos, AnalysisFail):
                analysis_fail = pos
            else:
                positions_filtrees.add(pos)

        positions_filtrees = resoudre_chevauchements(positions_filtrees, text)
        doc_hash = hash_any(file)

        redactor_context = RedactorContext()
        if params.get("mask", True):
            redactor_context.set_strategy(MaskRedactor())
        else:
            redactor_context.set_strategy(PseudonimiseRedactor(PSEUDO_VALUES))

        redacted_content = redactor_context.execute_strategy(file, positions_filtrees)

        author = PersonDAO().find_by_id(sent_by.id)

        # Si l'analyse a recontré un problème, on ne regarde que la source de l'erreur (llm ou regex ou llm as a judge s'il est implémenté apr exemple).
        # Il serait possible de détailler l'erreur, mais par simplicité l'utilisateur est seulement prévenu d'où se trouve la première erreur recontré.
        redacted_doc = RedactedDoc(doc_hash, datetime.now(), author.email, params, positions_filtrees, None, redacted_content, analysis_fail.source if analysis_fail is not None else None)
        DocDAO().register_document(redacted_doc)

        return redacted_doc

    @log
    def find_by_id(self, id: int, sent_by: Person) -> RedactedDoc:
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        doc = DocDAO().find_by_id(id)
        if doc is None:
            raise DocNotFound
        else:
            return doc

    @log
    def find_all(self, sent_by: Person):
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        docs = DocDAO().find_all()
        if docs == []:
            raise DocNotFound
        else:
            return docs
