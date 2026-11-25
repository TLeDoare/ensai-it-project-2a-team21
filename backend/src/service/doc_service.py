import asyncio
from datetime import date, datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.analyser.overlap import resoudre_chevauchements
from business_object.llm_client.injection_filter import InjectionFilter
from business_object.llm_client.injection_judge import SUSPECT, InjectionJudge
from business_object.llm_client.llm_client import anonymiser_directement
from business_object.person import Person
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from business_object.redactor.pseudonimise_redactor import PseudonimiseRedactor
from business_object.redactor.redactorcontext import RedactorContext
from business_object.types import Access, AnalysisFail
from dao.doc_dao import DocDAO
from dao.injection_attempt_dao import InjectionAttemptDAO
from dao.person_dao import PersonDAO
from service.person_service import PersonService
from utils.exceptions import DocNotFound, LLMInjectionError
from utils.log_utils import get_logger, log
from utils.security import hash_document

logger = get_logger(__name__)


class DocService:
    async def create(self, file: str, sent_by: Person, params: dict) -> RedactedDoc:
        logger.info(f"{sent_by.email} caviarde un document avec les paramètres {params}")
        PersonService().grant_auth(sent_by, Access.CreateDoc)
        # Détection d'injection
        injection_filter = InjectionFilter()
        if injection_filter.detect_injection(file):
            doc_hash = hash_document(file)
            logger.warning(f"!!! TENTATIVE D'INJECTION DE PROMPT DETECTEE !!! Par: {sent_by.email} (Hash: {doc_hash})")
            InjectionAttemptDAO().register_attempt(sent_by.email, doc_hash, "Pattern matching")
            # On peut décider de lever une exception ici pour bloquer le processus
            # raise SecurityException("Tentative d'injection détectée")
            raise LLMInjectionError

        text = file

        analyser = AnalyserFactory().get_analyser(params)
        params_journal = dict(params)
        if params.get("llm", True):
            # FO3 : le juge d'injection tourne en parallèle de la détection ; son verdict est
            # seulement enregistré dans le journal, il ne bloque jamais le caviardage
            positions, verdict = await asyncio.gather(analyser.analyse(text), InjectionJudge().juger(text))
            params_journal["juge_injection"] = verdict
            if verdict == SUSPECT:
                logger.warning(f"Le juge d'injection signale le document de {sent_by.email}")
                InjectionAttemptDAO().register_attempt(sent_by.email, hash_document(file), "Juge LLM")
        else:
            positions = await analyser.analyse(text)

        # On s'assure ici que l'analyse n'a pas rencontré de problème
        analysis_fail = []
        positions_filtrees = set()
        for pos in positions:
            if isinstance(pos, AnalysisFail):
                analysis_fail.append(pos)
            else:
                positions_filtrees.add(pos)

        positions_filtrees = resoudre_chevauchements(positions_filtrees, text)
        doc_hash = hash_document(file)

        redactor_context = RedactorContext()
        if params.get("mask", True):
            redactor_context.set_strategy(MaskRedactor())
        else:
            redactor_context.set_strategy(PseudonimiseRedactor())

        redacted_content = redactor_context.execute_strategy(file, positions_filtrees)

        author = PersonDAO().find_by_id(sent_by.id)

        # Si l'analyse rate, elle est convertie en chaîne de caractère pour être facilement retransmise à l'utilisateur
        redacted_doc = RedactedDoc(doc_hash, datetime.now(), author.email, params_journal, positions_filtrees, None, redacted_content, [af.to_str_tuple() for af in analysis_fail])
        DocDAO().register_document(redacted_doc)

        return redacted_doc

    async def anonymiser_par_llm(self, file: str, sent_by: Person, masquer: bool = True) -> str:
        """FO2 : le LLM réécrit lui-même le document anonymisé, pour le comparer au pipeline classique.

        Mêmes droits et même filtre d'injection que create. Rien n'est enregistré en base :
        sans positions, ce traitement fausserait les indicateurs du journal (F4).
        """
        logger.info(f"{sent_by.email} demande une anonymisation directe par le LLM")
        PersonService().grant_auth(sent_by, Access.CreateDoc)
        if InjectionFilter().detect_injection(file):
            doc_hash = hash_document(file)
            logger.warning(f"!!! TENTATIVE D'INJECTION DE PROMPT DETECTEE !!! Par: {sent_by.email} (Hash: {doc_hash})")
            InjectionAttemptDAO().register_attempt(sent_by.email, doc_hash, "Pattern matching")
            raise LLMInjectionError
        return await anonymiser_directement(file, masquer)

    @log
    def find_by_id(self, id: int, sent_by: Person) -> RedactedDoc:
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        doc = DocDAO().find_by_id(id)
        if doc is None:
            raise DocNotFound
        else:
            return doc

    @log
    def find_all(self, sent_by: Person, auteur: str | None = None, debut: date | None = None, fin: date | None = None):
        """Journal des traitements (F4), filtré par auteur et par période si ces paramètres sont donnés."""
        PersonService().grant_auth(sent_by, Access.ReadDoc)
        docs = DocDAO().find_all(auteur, debut, fin)
        if docs == []:
            raise DocNotFound
        else:
            return docs
