from typing import Annotated

from ast import literal_eval

from fastapi import APIRouter, Depends, Form, File

from schema.doc_model import DocModel, UploadDocModel
from service.doc_service import DocService
from utils.security import verify_token

router = APIRouter()


def get_doc_service():
    """Dependency provider for DocService."""
    return DocService()


@router.post("/redact/", response_model=DocModel, status_code=201, tags=["Doc"])
async def televerser_doc(
        file: Annotated[bytes, File()],
        params: Annotated[str, Form()] = "{}",
        doc_service=Depends(get_doc_service),
        current_person=Depends(verify_token)):
    # L'objet req contient le fichier et les paramètres (stratégie, etc.)
    doc_traite = await doc_service.create(file.decode("utf-8"), current_person.id, literal_eval(params))
    return doc_traite
