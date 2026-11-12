from datetime import datetime

from business_object.person import Person
from business_object.types import AnalysisFails, Positions


class RedactedDoc:
    def __init__(self, hash: str, upload_date: datetime, sent_by: Person, params: dict, details: Positions, id: int | None = None, content: str | None = None, analysis_fail_source: AnalysisFails = []):
        self.content = content
        self.hash = hash
        self.upload_date = upload_date
        self.sent_by = sent_by
        self.params = params
        self.details = details
        self.id = id
        self.analysis_fail_source = analysis_fail_source
