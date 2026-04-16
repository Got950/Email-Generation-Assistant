import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import evaluate, generate
from app.config import get_settings

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


@asynccontextmanager
async def lifespan(app: FastAPI):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    s = get_settings()
    logging.basicConfig(
        level=getattr(logging, s.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    log = logging.getLogger(__name__)
    log.info(
        "Email Generation Assistant started | provider=%s primary=%s baseline=%s",
        s.resolved_provider,
        s.get_model_name("primary"),
        s.get_model_name("baseline"),
    )
    if not s.has_valid_key:
        log.warning("No valid API key detected — generation and evaluation will fail")
    yield


app = FastAPI(
    title="Email Generation Assistant",
    description="AI-powered professional email generator with evaluation framework",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, tags=["Generation"])
app.include_router(evaluate.router, tags=["Evaluation"])


@app.get("/health")
async def health():
    s = get_settings()
    return {
        "status": "ok",
        "provider": s.resolved_provider,
        "has_valid_key": s.has_valid_key,
    }
