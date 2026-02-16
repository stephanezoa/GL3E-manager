"""
Main FastAPI application
"""
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.database import init_db
from app.database import SessionLocal
from app.models import Student
from app.routers import student, admin, auth
from app.config import settings
from app.logging_config import (
    configure_root_logging,
    get_endpoint_logger,
    get_error_logger,
    get_ingress_logger,
)

# Configure root console logging
configure_root_logging(settings.DEBUG)

logger = logging.getLogger(__name__)
error_logger = get_error_logger()
ingress_logger = get_ingress_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Système d'attribution de projets pour la classe GL3E",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
allow_all_origins = "*" in cors_origins
if allow_all_origins:
    # Fully distributed mode: accept every external origin.
    # Use regex to keep credentialed requests working across origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Basic production hardening middlewares
allowed_hosts = [h.strip() for h in settings.ALLOWED_HOSTS.split(",") if h.strip()]
if allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(student.router, tags=["Student"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])


def _wants_html(request: Request) -> bool:
    accept = (request.headers.get("accept") or "").lower()
    return "text/html" in accept


@app.middleware("http")
async def endpoint_logging_middleware(request: Request, call_next):
    """Log each endpoint request/response to endpoint-specific files."""
    request_id = str(uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    method = request.method
    path = request.url.path
    query = request.url.query
    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else None) or (
        request.client.host if request.client else None
    )
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    host = request.headers.get("host")
    referer = request.headers.get("referer")
    scheme = request.url.scheme

    endpoint_logger = get_endpoint_logger(method, path)
    ingress_logger.info(
        "request_received",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "query": query,
            "client_ip": client_ip,
            "real_ip": real_ip,
            "forwarded_for": forwarded_for,
            "host": host,
            "scheme": scheme,
            "referer": referer,
            "user_agent": user_agent,
        },
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 3)

        endpoint_logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "real_ip": real_ip,
                "forwarded_for": forwarded_for,
                "host": host,
                "scheme": scheme,
                "referer": referer,
                "user_agent": user_agent,
                "success": response.status_code < 400,
            },
        )
        return response
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 3)
        request.state.error_logged = True

        endpoint_logger.error(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "status_code": 500,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "real_ip": real_ip,
                "forwarded_for": forwarded_for,
                "host": host,
                "scheme": scheme,
                "referer": referer,
                "user_agent": user_agent,
                "success": False,
            },
        )

        error_logger.exception(
            "unhandled_exception",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "client_ip": client_ip,
                "real_ip": real_ip,
                "forwarded_for": forwarded_for,
                "host": host,
                "scheme": scheme,
                "referer": referer,
                "user_agent": user_agent,
            },
        )

        # Do not re-raise: keep failure isolated to this request.
        if _wants_html(request):
            try:
                return templates.TemplateResponse(
                    "errors/500.html",
                    {"request": request, "request_id": request_id},
                    status_code=500,
                )
            except Exception:
                return HTMLResponse(content="<h1>500 - Erreur interne</h1>", status_code=500)

        return JSONResponse(
            status_code=500,
            content={"detail": "Une erreur interne est survenue", "request_id": request_id},
        )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions without impacting the rest of the app."""
    request_id = getattr(request.state, "request_id", str(uuid4()))
    method = request.method
    path = request.url.path
    query = request.url.query
    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else None) or (
        request.client.host if request.client else None
    )
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # 4xx are part of normal flow for many APIs, so keep this as warning.
    if exc.status_code >= 400:
        endpoint_logger = get_endpoint_logger(method, path)
        endpoint_logger.warning(
            "http_exception",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "status_code": exc.status_code,
                "client_ip": client_ip,
                "real_ip": real_ip,
                "forwarded_for": forwarded_for,
                "user_agent": user_agent,
                "success": False,
                "error": str(exc.detail),
            },
        )

    if exc.status_code == 404 and _wants_html(request):
        try:
            return templates.TemplateResponse(
                "errors/404.html",
                {"request": request, "path": path},
                status_code=404,
            )
        except Exception:
            # If template rendering fails, return a safe plain response.
            return HTMLResponse(
                content="<h1>404 - Page introuvable</h1>",
                status_code=404,
            )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info(f"Application started in {'DEBUG' if settings.DEBUG else 'PRODUCTION'} mode")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global fallback handler for unhandled exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid4()))
    method = request.method
    path = request.url.path
    query = request.url.query
    forwarded_for = request.headers.get("x-forwarded-for")
    real_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else None) or (
        request.client.host if request.client else None
    )
    client_ip = request.client.host if request.client else None
    host = request.headers.get("host")
    referer = request.headers.get("referer")
    scheme = request.url.scheme
    user_agent = request.headers.get("user-agent")

    if not getattr(request.state, "error_logged", False):
        exc_info = (type(exc), exc, exc.__traceback__)
        error_logger.exception(
            "unhandled_exception",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "client_ip": client_ip,
                "real_ip": real_ip,
                "forwarded_for": forwarded_for,
                "host": host,
                "scheme": scheme,
                "referer": referer,
                "user_agent": user_agent,
            },
            exc_info=exc_info,
        )

    if _wants_html(request):
        try:
            return templates.TemplateResponse(
                "errors/500.html",
                {"request": request, "request_id": request_id},
                status_code=500,
            )
        except Exception:
            return HTMLResponse(
                content="<h1>500 - Erreur interne</h1>",
                status_code=500,
            )

    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue", "request_id": request_id},
    )


@app.get("/")
async def root(request: Request):
    """Home page - student interface"""
    students: list[dict[str, str | int]] = []
    db = SessionLocal()
    try:
        db_students = db.query(Student).order_by(Student.full_name).all()
        students = [
            {"id": s.id, "name": s.full_name, "matricule": s.matricule}
            for s in db_students
        ]
    finally:
        db.close()

    return templates.TemplateResponse("index.html", {"request": request, "students": students})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
