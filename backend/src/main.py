from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from controller import doc_controller, login_controller, person_controller
from utils.env_variables import load_environment_variables
from utils.log_utils import LogMiddleware, get_logger, initialize_logs
from utils.reset_database import ResetDatabase

logger = get_logger(__name__)
initialize_logs("Anonymia Webservice")

app = FastAPI(title="Anonymia Webservice")
app.add_middleware(LogMiddleware)

load_environment_variables()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepts Pydantic 422 errors to log them.
    """
    logger.error("Validation Error.")

    # On renvoie une réponse à l'utilisateur, mais l'erreur précise est cachée des logs.
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect to the API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/reset_database", tags=["Misc"])
async def reset_database():
    """Reset the database"""
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
