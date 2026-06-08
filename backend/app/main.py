from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="Barcode Generation API")

app.include_router(api_router)
