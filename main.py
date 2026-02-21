"""
Kazakh Language Learning Virtual Assistant - Main application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.lessons.router import router as lessons_router
from app.exercises.router import router as exercises_router
from app.tests.router import router as tests_router
from app.assistant.router import router as assistant_router
from app.vocabulary.router import router as vocabulary_router
from app.progress.router import router as progress_router
from app.recommendations.router import router as recommendations_router
from app.logging_mod.router import router as logs_router
from app.files.router import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Kazakh Language Learning Virtual Assistant",
    description="Дипломный проект: Разработка виртуального помощника для интерактивного изучения казахского языка",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(exercises_router, prefix="/api")
app.include_router(tests_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(vocabulary_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(files_router, prefix="/api")

# Serve frontend static assets
app.mount("/static", StaticFiles(directory="frontend"), name="static")

from pathlib import Path
from fastapi.responses import FileResponse

FRONTEND = Path("frontend")


def serve_page(name: str):
    path = FRONTEND / f"{name}.html"
    if path.exists():
        return FileResponse(path)
    return FileResponse(FRONTEND / "login.html")


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "login.html")


@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND / "login.html")


@app.get("/register")
async def register_page():
    return FileResponse(FRONTEND / "register.html")


@app.get("/dashboard")
@app.get("/lessons")
@app.get("/exercises")
@app.get("/tests")
@app.get("/chat")
@app.get("/vocabulary")
@app.get("/progress")
@app.get("/admin")
async def app_pages():
    return FileResponse(FRONTEND / "dashboard.html")


@app.get("/lesson/{lesson_id}")
async def lesson_page(lesson_id: int):
    return FileResponse(FRONTEND / "dashboard.html")


@app.get("/api/health")
async def api_health():
    return {"app": "Kazakh Language Learning Assistant", "version": "1.0"}
