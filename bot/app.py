from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router as api_router
from config import CORS_ORIGINS, TEMP_FOLDER, UPLOAD_FOLDER, VECTOR_DB_PATH


APP_NAME = "Web Knowledge Bot Backend"
APP_VERSION = "1.0.0"
API_PREFIX = ""


def ensure_runtime_directories() -> None:
    """Create local storage directories required by uploads and ChromaDB."""
    for directory in (UPLOAD_FOLDER, VECTOR_DB_PATH, TEMP_FOLDER):
        Path(directory).mkdir(parents=True, exist_ok=True)


def include_api_routes(application: FastAPI) -> None:
    """Mount project API routes on the application."""
    application.router.routes.extend(api_router.routes)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare application resources during startup."""
    ensure_runtime_directories()
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=(
            "Backend API for PDF-based Retrieval-Augmented Generation, "
            "Gemini response generation, chat history, and future website "
            "retriever integration."
        ),
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    include_api_routes(application)

    @application.get("/", tags=["System"])
    async def root() -> dict[str, str]:
        return {
            "service": APP_NAME,
            "version": APP_VERSION,
            "status": "running",
        }

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "path": request.url.path,
                "detail": str(exc),
            },
        )

    return application


app = create_app()
