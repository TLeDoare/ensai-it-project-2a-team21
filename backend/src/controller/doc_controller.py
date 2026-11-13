from ast import literal_eval
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException

from schema.doc_model import DocModel
from service.doc_service import DocService
from utils.exceptions import (
    AuthError,
    DocNotFound,
    DocRegistrationError,
    PseudonymisationImpossible,
    RedactorError,
)
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
    try:
        fichier = file.decode("utf-8")
        if len(fichier) < 20000:
            doc_traite = await doc_service.create(fichier, current_person, literal_eval(params))
            return doc_traite
        else:
            raise HTTPException(status_code=500, detail="Le fichier est trop volumineux.")
    except DocRegistrationError:
        raise HTTPException(status_code=500, detail="Le document téléversé est trop lourd.") from DocRegistrationError
    except UnicodeDecodeError:
        raise HTTPException(status_code=500, detail="Le document est dans un format inconnu. Veuillez téléverser un document de format .md ou .txt et valide au sens unicode.") from DocRegistrationError
    except RedactorError:
        raise HTTPException(status_code=500, detail="Le processus de caviardage a recontré un problème.") from RedactorError
    except PseudonymisationImpossible as erreur:
        raise HTTPException(
            status_code=409,
            detail=str(erreur)
        ) from erreur

@router.post("/find_by_id", response_model=DocModel, tags=["Doc"])
async def find_by_id(id: int, doc_service=Depends(get_doc_service), current_person=Depends(verify_token)):
    try:
        return doc_service.find_by_id(id, current_person)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

@router.post("/find_all", response_model=list[DocModel], tags=["Doc"])
async def find_all(doc_service=Depends(get_doc_service), current_person=Depends(verify_token)):
    try:
        return doc_service.find_all(current_person)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

