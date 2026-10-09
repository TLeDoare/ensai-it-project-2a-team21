from utils.log_utils import log
from datetime import datetime
from business_object.redacted_doc import RedactedDoc
from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.redactor.mask_redactor import MaskRedactor
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO


class DocService:

    # dans le futur, file sera UploadFile et non str
    @log
    def create(self, file: str, sent_by: int, params: dict):
        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = analyser.analyse(text)

        redactor = MaskRedactor()
        redacted_content = redactor.redact(text, positions)

        author = PersonDAO().find_by_id(sent_by)

        #f = open("test", "wb")
        #f.write(redacted_content)
        print("========================")
        print(redacted_content)
        print("========================")

        redacted_doc = RedactedDoc("test", datetime.now(), author, params, positions, None)
        DocDAO().register_document(redacted_doc, sent_by)

        return redacted_doc


