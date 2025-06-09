from fastapi import FastAPI
from app.routers import bots

app = FastAPI()

app.include_router(bots.router, prefix="/bots", tags=["Bots"])

@app.get("/")
def read_root():
    return {"message": "DCA Bot Backend running"}
