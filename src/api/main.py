# -*- coding: utf-8 -*-
"""
FastAPI main application — AI Sports Coach PWA Backend.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.utils.config import settings
from src.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application."""
    logger.info("=== AI Sports Coach API — Démarrage ===")
    yield
    logger.info("=== AI Sports Coach API — Arrêt ===")


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI."""
    setup_logging()

    app = FastAPI(
        title="AI Sports Coach API",
        description="Backend API pour l'assistant d'entraînement IA",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────

    from src.api.auth import router as auth_router
    from src.api.chat import router as chat_router
    from src.api.profile import router as profile_router

    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(profile_router)

    from src.api.dashboard import router as dashboard_router
    from src.api.athlete import router as athlete_router
    from src.api.onboarding import router as onboarding_router
    from src.api.feedback import router as feedback_router

    app.include_router(dashboard_router)
    app.include_router(athlete_router)
    app.include_router(onboarding_router)
    app.include_router(feedback_router)

    # ── Routes de base ───────────────────────────────────────────────

    @app.get("/api/health")
    async def health_check():
        """Health check — retourne l'état du service."""
        return {
            "status": "ok",
            "version": "0.1.0",
        }

    # ── Gestionnaire d'exceptions global ─────────────────────────────

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Capture toutes les exceptions non gérées."""
        logger.error(
            "Exception non gérée: %s | path=%s",
            exc,
            request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Erreur interne du serveur"},
        )

    return app


app = create_app()
