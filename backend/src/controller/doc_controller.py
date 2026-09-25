from fastapi import APIRouter, Depends

from schema.doc_model import DocModel, UploadDocModel
from service.doc_service import DocService

router = APIRouter()

def get_doc_service():
    """Dependency provider for GameService."""
    return DocService()


@router.post("/", response_model=DocModel, tags=["Doc"])
def televerser_doc(req: UploadDocModel):
    pass