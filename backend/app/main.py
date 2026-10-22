"""
FastAPI Main Application Entrypoint for NWP Forecast Bust Detection & Confidence System.
"""
from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.api.endpoints import router as forecast_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.environ.get("PORT", "8000")
    print("=" * 65)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} Starting Up on port {port}")
    print(f"   Domain: South Asia ({settings.LAT_MIN}°N - {settings.LAT_MAX}°N, {settings.LON_MIN}°E - {settings.LON_MAX}°E)")
    print(f"   API Docs available at: /docs")
    print("=" * 65)
    yield
    print(f"🛑 {settings.PROJECT_NAME} Shutting Down")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Operational Medium-Range NWP Forecast Bust Detection and Lead-Time Confidence System.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(forecast_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint for container orchestrators (Render/Docker/Kubernetes)."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "scenarios_ready": len(settings.SCENARIOS)
    }

# Frontend static asset serving (Single-Container / Render deployment)
FRONTEND_DIR = Path("/app/frontend_dist")
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa_frontend(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/", tags=["System"])
    def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} Operational API",
            "docs_url": "/docs",
            "health_url": "/health",
            "endpoints": {
                "summary": f"{settings.API_V1_PREFIX}/forecast/summary",
                "grid": f"{settings.API_V1_PREFIX}/forecast/grid",
                "explain": f"{settings.API_V1_PREFIX}/forecast/explain",
                "scenarios": f"{settings.API_V1_PREFIX}/forecast/scenarios",
                "infer": f"{settings.API_V1_PREFIX}/forecast/infer"
            }
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
