"""
LifeLink Blood Donor Matching API — production-hardened entry point.

Features added:
- Structured JSON logging
- Sentry error monitoring
- Rate limiting (slowapi)
- Security headers middleware
- Request logging middleware
- Proper CORS from env variable
- Connection pool for DB
- /health endpoint for uptime checks
"""
import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.blood_banks import router as blood_banks_router
from app.api.v1.donors import router as donors_router
from app.api.v1.matches import router as matches_router
from app.api.v1.requests import router as requests_router

# ── 1. Logging ───────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ── 2. Sentry (only when DSN is configured) ──────────────────────────────────
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.2,      # capture 20% of transactions
        profiles_sample_rate=0.1,
        send_default_pii=False,      # never send user PII to Sentry
    )
    logger.info("Sentry initialised for environment: %s", settings.ENVIRONMENT)

# ── 3. App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="LifeLink Blood Donor Matching API",
    version="1.0.0",
    description="Emergency blood donor matching by blood type and geo-proximity.",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ── 4. Rate limiting ─────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── 5. Security & logging middleware ─────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ── 6. CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 7. Routers ───────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(donors_router)
app.include_router(requests_router)
app.include_router(matches_router)
app.include_router(blood_banks_router)

# ── 8. Global exception handler ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Our team has been notified."},
    )

# ── 9. Health check ───────────────────────────────────────────────────────────
@app.get("/health", tags=["system"], summary="Health check for uptime monitors")
def health_check():
    """Returns 200 when the API is running. Used by Railway / Render health checks."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/", tags=["system"])
def read_root():
    return {"message": "LifeLink Blood Donor API", "version": "1.0.0"}
