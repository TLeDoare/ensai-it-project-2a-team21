from datetime import datetime

from business_object.person import Person
from business_object.types import Positions


class RedactedDoc:
    def __init__(self, filename: str, upload_date: datetime, sent_by: Person, params: dict, details: Positions, id: int | None = None, file_path: str = None):
        self.filename = filename
        self.upload_date = upload_date
        self.sent_by = sent_by
        self.params = params
        self.details = details
        self.id = id
