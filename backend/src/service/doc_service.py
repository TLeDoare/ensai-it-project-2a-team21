from utils.log_utils import log
from datetime import datetime
from business_object.redacted_doc import RedactedDoc
from business_object.analyser.analyser_factory import AnalyserFactory
from business_object.redactor.mask_redactor import MaskRedactor


class DocService:

    # dans le futur, file sera UploadFile et non str
    # sent_by devrait etre Person
    @log
    def create(self, file: str, sent_by: int, params: dict):
        text = file

        analyser = AnalyserFactory().get_analyser(params)
        positions = analyser.analyse(text)

        redactor = MaskRedactor()
        redacted_content = redactor.redact(text, positions)

        #f = open("test", "wb")
        #f.write(redacted_content)
        print(redacted_content)

        return RedactedDoc("test", datetime.now(), sent_by, params, positions, None)


