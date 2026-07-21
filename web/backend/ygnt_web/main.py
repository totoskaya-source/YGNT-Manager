from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ygnt_web.api.auth import router as auth_router
from ygnt_web.api.health import router as health_router
from ygnt_web.api.prestations import router as prestations_router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="YGNT Manager Web")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(prestations_router)

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
