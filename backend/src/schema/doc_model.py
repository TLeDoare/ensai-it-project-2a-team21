from datetime import datetime

from pydantic import BaseModel


class UploadDocModel(BaseModel):
    file: str  # Devrait être UploadFile
    sent_by: int
    params: dict


class DocModel(BaseModel):
    filename: str
    upload_date: datetime
    sent_by: int
    id: int | None
    params: dict
