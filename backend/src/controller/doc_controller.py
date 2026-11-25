from ast import literal_eval
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException

from schema.doc_model import DocModel
from service.doc_service import DocService
from utils.exceptions import (
    AuthError,
    DocNotFound,
    DocRegistrationError,
    LLMInjectionError,
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
        try:
            parsed_params = literal_eval(params)
        except ValueError:
            raise HTTPException(status_code=422, detail="Les paramètres sont à fournir en format Python plutôt que JSON (e.g. true -> True)") from ValueError
        if len(fichier) < 20000:
            doc_traite = await doc_service.create(fichier, current_person, parsed_params)
            return doc_traite
        else:
            raise HTTPException(status_code=413, detail="Le fichier est trop volumineux.")
    except DocRegistrationError:
        raise HTTPException(status_code=413, detail="Le document téléversé est trop lourd.") from DocRegistrationError
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Le document est dans un format inconnu. Veuillez téléverser un document de format .md ou .txt et valide au sens unicode.") from DocRegistrationError
    except RedactorError:
        raise HTTPException(status_code=500, detail="Le processus de caviardage a recontré un problème.") from RedactorError
    except PseudonymisationImpossible as erreur:
        raise HTTPException(
            status_code=409,
            detail=str(erreur)
        ) from erreur
    except LLMInjectionError:
        raise HTTPException(status_code=400, detail="Une injection de LLM a été détectée.") from LLMInjectionError

@router.post("/redact_llm/", tags=["Doc"])
async def anonymiser_par_llm(
        file: Annotated[bytes, File()],
        mask: Annotated[bool, Form()] = True,
        doc_service=Depends(get_doc_service),
        current_person=Depends(verify_token)):
    """FO2 : renvoie le document réécrit par le LLM, pour comparaison avec le caviardage classique."""
    # Mêmes contrôles d'entrée que /redact/ : texte UTF-8 de moins de 20 000 caractères
    try:
        fichier = file.decode("utf-8")
    except UnicodeDecodeError as erreur:
        raise HTTPException(status_code=415, detail="Le document doit être un texte valide au sens unicode (.md ou .txt).") from erreur
    if len(fichier) >= 20000:
        raise HTTPException(status_code=413, detail="Le fichier est trop volumineux.")

    try:
        # mask suit la stratégie choisie pour le caviardage classique : la comparaison reste équitable
        contenu = await doc_service.anonymiser_par_llm(fichier, current_person, mask)
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError
    except LLMInjectionError:
        raise HTTPException(status_code=400, detail="Une injection de LLM a été détectée.") from LLMInjectionError
    except Exception as erreur:
        # LLM injoignable, clé absente, délai dépassé : ce mode n'a pas de solution de repli
        raise HTTPException(status_code=503, detail="Le LLM n'a pas pu produire le document anonymisé.") from erreur
    return {"content": contenu}


@router.post("/find_by_id", response_model=DocModel, tags=["Doc"])
async def find_by_id(id: int, doc_service=Depends(get_doc_service), current_person=Depends(verify_token)):
    try:
        return doc_service.find_by_id(id, current_person)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

@router.post("/find_all", response_model=list[DocModel], tags=["Doc"])
async def find_all(
    auteur: str | None = None,
    debut: date | None = None,
    fin: date | None = None,
    doc_service=Depends(get_doc_service),
    current_person=Depends(verify_token),
):
    """Journal des traitements (F4). Filtres facultatifs : e-mail de l'auteur, date de début et date de fin
    (format AAAA-MM-JJ, dates incluses). Sans filtre, tout le journal est renvoyé."""
    if debut and fin and debut > fin:
        raise HTTPException(status_code=400, detail="La date de début doit précéder la date de fin.")
    try:
        return doc_service.find_all(current_person, auteur, debut, fin)
    except DocNotFound:
        raise HTTPException(status_code=404, detail="Ce document n'existe pas") from DocNotFound
    except AuthError:
        raise HTTPException(status_code=401, detail="Accès non autorisé.") from AuthError

