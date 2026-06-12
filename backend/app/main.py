from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import sessionmaker

from backend.app.api import error_payload, router
from backend.app.config import ROOT_DIR, get_settings
from backend.app.db import init_db
from backend.app.db import SessionLocal as DefaultSessionLocal

FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"


def validation_error_code(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "validation.request.invalid"
    first_error = errors[0]
    location = [
        str(part)
        for part in first_error.get("loc", ())
        if part not in {"body", "query", "path"}
    ]
    field_path = ".".join(location) if location else "request"
    error_type = str(first_error.get("type", "invalid")).replace("_error", "")
    return f"validation.{field_path}.{error_type}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if app.state.initialize_database:
        init_db()
    yield


def create_app(
    session_factory: sessionmaker | None = None,
    initialize_database: bool = True,
) -> FastAPI:
    api_app = FastAPI(title="Renovation Estimator API", lifespan=lifespan)
    api_app.state.SessionLocal = session_factory or DefaultSessionLocal
    api_app.state.initialize_database = initialize_database
    api_app.state.uploads_dir = get_settings().uploads_dir
    api_app.include_router(router)

    @api_app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=error_payload(exc.detail["code"], exc.detail["message"]))
        return JSONResponse(status_code=exc.status_code, content=error_payload("http_error", str(exc.detail)))

    @api_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload(validation_error_code(exc), "Validation failed"),
        )

    # Serve the built SPA when present (production image). The catch-all is
    # registered after the API router, so /api/* keeps priority. Unknown
    # non-API paths fall back to index.html for client-side routing.
    if FRONTEND_DIST.is_dir():
        index_file = FRONTEND_DIST / "index.html"

        @api_app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            if full_path.startswith("api"):
                raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})
            if full_path:
                candidate = (FRONTEND_DIST / full_path).resolve()
                if candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST.resolve()):
                    return FileResponse(candidate)
            return FileResponse(index_file)

    return api_app


app = create_app()
