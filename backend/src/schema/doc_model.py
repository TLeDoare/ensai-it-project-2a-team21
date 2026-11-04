from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from business_object.types import PII, Analyser


class UploadDocModel(BaseModel):
    params: str


class PositionModel(BaseModel):
    start: int
    end: int
    type: str
    confidence: float
    source: str


class DocModel(BaseModel):
    hash: str
    upload_date: datetime
    sent_by: EmailStr
    id: int | None
    params: dict
    details: list[PositionModel]
    content: str | None

    @field_validator("details", mode="before")
    @classmethod
    def rendre_lisible(cls, positions):
        return [
            {
                "start": p[0][0],
                "end": p[0][1],
                "type": PII(p[1]).name,
                "confidence": p[2],
                "source": Analyser(p[3]).name,
            }
            for p in positions
        ]