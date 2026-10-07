from fastapi import FastAPI
from controller import doc_controller

app = FastAPI(title="Anonymia Webservice")

@app.get("/")
async def root():
    return {"message": "bonjour"}

app.include_router(doc_controller.router, prefix="/doc", tags=["Doc"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
    )
