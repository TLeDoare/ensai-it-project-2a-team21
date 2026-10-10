from fastapi import FastAPI
from controller import doc_controller
from controller import login_controller
from utils.log_utils import get_logger
from utils.reset_database import ResetDatabase

logger = get_logger(__name__)

app = FastAPI(title="Anonymia Webservice")

@app.get("/")
async def root():
    return {"message": "bonjour"}


@app.get("/reset_database", tags=["Misc"])
async def reset_database():
    """Reset the database"""
    logger.info("Database reset")
    success = ResetDatabase().run()

    return {"message": f"Database re-initialization - {'SUCCESS' if success else 'FAILURE'}"}


app.include_router(doc_controller.router, prefix="/doc", tags=["Doc"])
app.include_router(login_controller.router, prefix="/login", tags=["Login"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
    )
