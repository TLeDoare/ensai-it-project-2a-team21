from fastapi import FastAPI

app = FastAPI(title="Anonymia Webservice")

@app.get("/")
async def root():
    return {"message": "bonjour"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
    )
