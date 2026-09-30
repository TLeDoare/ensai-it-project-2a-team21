from fastapi import APIRouter, Depends

from schema.doc_model import DocModel, UploadDocModel
from service.doc_service import DocService

router = APIRouter()


def get_doc_service():
    """Dependency provider for DocService."""
    return DocService()


@router.post("/redact", response_model=DocModel, status_code=201, tags=["Doc"])
def televerser_doc(req: UploadDocModel, doc_service: DocService = Depends(get_doc_service)):
    # L'objet req contient le fichier et les paramètres (stratégie, etc.)
    doc_traite = doc_service.create(req, sent_by, params)
    return doc_traite
