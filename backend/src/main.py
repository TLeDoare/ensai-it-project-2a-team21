from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from business_object.types import Role
from controller import doc_controller, login_controller, person_controller
from utils.env_variables import load_environment_variables
from utils.log_utils import LogMiddleware, get_logger, initialize_logs
from utils.reset_database import ResetDatabase
from utils.security import verify_token

logger = get_logger(__name__)
initialize_logs("Anonymia Webservice")

app = FastAPI(title="Anonymia Webservice")
app.add_middleware(LogMiddleware)

load_environment_variables()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepte les erreurs de validation Pydantic (422).

    Ni les logs ni la réponse ne contiennent les valeurs envoyées (ER1-04) : une requête
    mal formée peut contenir un mot de passe ou un extrait de document.
    """
    logger.error("Validation Error.")

    # Pour chaque erreur, on garde seulement le champ concerné (loc), le message (msg)
    # et le type d'erreur (type) ; la valeur reçue (input) n'est jamais renvoyée.
    erreurs = [
        {"loc": erreur["loc"], "msg": erreur["msg"], "type": erreur["type"]}
        for erreur in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": erreurs},
    )


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect to the API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/reset_database", tags=["Misc"])
async def reset_database(current_person=Depends(verify_token)):
    """Réinitialise la base de données (administrateur uniquement)."""
    # Seul un administrateur connecté peut vider la base : on refuse tous les autres rôles
    if current_person.role != Role.Administrateur:
        logger.warning("Tentative de réinitialisation de la base refusée")
        raise HTTPException(status_code=403, detail="Action non autorisée.")

    logger.info("Database reset")
    success = ResetDatabase().run()

    return {"message": f"Database re-initialization - {'SUCCESS' if success else 'FAILURE'}"}

app.include_router(doc_controller.router, prefix="/doc", tags=["Doc"])
app.include_router(login_controller.router, prefix="/login", tags=["Login"])
app.include_router(person_controller.router, prefix="/person", tags=["Users"])

if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=int(os.getenv("UVICORN_PORT", "5000")),
    )
