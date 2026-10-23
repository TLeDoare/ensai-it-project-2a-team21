import asyncio

from datetime import datetime

from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.redacted_doc import RedactedDoc
from business_object.redactor.mask_redactor import MaskRedactor
from dao.doc_dao import DocDAO
from dao.person_dao import PersonDAO
from utils.log_utils import log
from utils.security import hash_any


class DocService:

    # dans le futur, file sera UploadFile et non str
    @log
    async def create(self, file: str, sent_by: int, params: dict):
        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = await analyser.analyse(text)
        hash = hash_any(file)

        redactor = MaskRedactor()
        redacted_content = redactor.redact(text, positions)

        author = await PersonDAO().find_by_id(sent_by)

        #f = open("test", "wb")
        #f.write(redacted_content)
        print("========================")
        print(redacted_content)

        redacted_doc = RedactedDoc("test", datetime.now(), author.email, params, positions, hash, None)
        DocDAO().register_document(redacted_doc, sent_by)
        print(list(redacted_doc.details)[0])
        print("========================")

        return redacted_doc
