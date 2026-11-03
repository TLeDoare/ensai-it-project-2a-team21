from datetime import datetime

from pydantic import BaseModel, EmailStr

from business_object.types import Position


class UploadDocModel(BaseModel):
    params: str


class DocModel(BaseModel):
    hash: str
    upload_date: datetime
    sent_by: EmailStr
    id: int | None
    params: dict
    details: list[Position]
    content: str | None
