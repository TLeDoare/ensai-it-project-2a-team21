from ast import literal_eval
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException

from schema.doc_model import DocModel
from service.doc_service import DocService
from utils.exceptions import AuthError, DocNotFound
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

@router.post("/find_by_id", response_model=DocModel, tags=["Doc"])
async def find_by_id(id: int, doc_service=Depends(get_doc_service), current_person=Depends(verify_token)):
    try:
        return DocService().find_by_id(id, current_person.id)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

@router.post("/find_all", response_model=list[DocModel], tags=["Doc"])
async def find_all(doc_service=Depends(get_doc_service), current_person=Depends(verify_token)):
    try:
        return DocService().find_all(current_person.id)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

