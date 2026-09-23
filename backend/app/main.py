from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import root_router, router
from backend.app.core.config import settings
from backend.app.core.logging import configure_logging
from backend.app.database.database import init_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_database()
    yield


app = FastAPI(
    title="AeroBust",
    version="0.1.0",
    description="Synthetic-first AI forecast-bust assessment API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)
app.include_router(router)
app.include_router(root_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


FRONTEND_DIR = Path("/app/frontend_dist")
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_root() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(FRONTEND_DIR / "index.html")