from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routes.resume import router as resume_router
from app.models.schemas import HealthResponse

FRONTEND_DIR = Path(__file__).parent / "frontend"


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"✅  Database initialized.")
    print(f"🚀  {settings.APP_NAME} is ready.")
    print(f"🌐  Frontend → http://localhost:8000")
    print(f"📖  API Docs → http://localhost:8000/docs")
    yield
    print("🛑  Shutting down...")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered resume analyzer using Gemini 2.5 Flash. "
        "Upload a PDF resume and receive an ATS score, strengths, weaknesses, "
        "missing keywords, and predicted interview questions."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes (must be registered BEFORE static mount) ───────────────────────
app.include_router(resume_router)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version="2.0.0",
    )


# ── Frontend (root serves index.html) ─────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_frontend():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return JSONResponse({"message": f"Welcome to {settings.APP_NAME} API", "docs": "/docs"})


# ── Static files fallback (CSS/JS/images if added later) ──────────────────────
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )