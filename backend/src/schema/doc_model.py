from datetime import datetime

from pydantic import BaseModel, EmailStr


class UploadDocModel(BaseModel):
    params: str


class DocModel(BaseModel):
    filename: str
    upload_date: datetime
    sent_by: EmailStr
    id: int | None
    params: dict
