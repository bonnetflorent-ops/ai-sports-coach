# -*- coding: utf-8 -*-
"""
Auth API — inscription, connexion, rafraîchissement de token, profil.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, field_validator

from src.db import get_supabase_admin, get_supabase
from src.db.users import get_user_by_email, create_user, get_user_by_id
from src.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Modèles de requête ──────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Email invalide")
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v

    @field_validator("first_name")
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        if len(v.strip()) < 1 or len(v.strip()) > 100:
            raise ValueError("Le prénom doit contenir entre 1 et 100 caractères")
        return v.strip()


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Helpers ─────────────────────────────────────────────────────────


def _supabase_admin():
    """Retourne un client Supabase avec la clé service_role."""
    return get_supabase_admin()


def _sign_in_with_password(email: str, password: str):
    """
    Connecte un utilisateur avec email et mot de passe.
    Retourne la session (access_token, refresh_token, user).
    """
    # Note: on utilise un client avec la clé anon pour le sign-in
    client = get_supabase()
    return client.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })


def _refresh_session(refresh_token: str):
    """Rafraîchit un token d'accès."""
    client = get_supabase()
    return client.auth.refresh_session(refresh_token)


# ── Endpoints ───────────────────────────────────────────────────────


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Crée un compte utilisateur via Supabase Auth + profile dans la table users.
    Retourne les tokens d'accès.
    """
    # Vérifier si l'email existe déjà
    existing = get_user_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )

    admin = _supabase_admin()

    try:
        # Créer l'utilisateur dans Supabase Auth
        auth_response = admin.auth.admin.create_user({
            "email": request.email,
            "password": request.password,
            "email_confirm": True,
        })
    except Exception as e:
        logger.error("Erreur création auth: %s", e)
        error_detail = str(e)
        if "already registered" in error_detail.lower() or "duplicate" in error_detail.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un compte avec cet email existe déjà",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte",
        )

    if not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte",
        )

    user_id = auth_response.user.id
    email = auth_response.user.email or request.email

    try:
        # Sauvegarder le profil dans la table users
        create_user(user_id, email, request.first_name)
    except Exception as e:
        logger.error("Erreur création profil: %s", e)
        # Tentative de rollback : supprimer l'utilisateur auth
        try:
            admin.auth.admin.delete_user(user_id)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du profil",
        )

    # Connecter l'utilisateur pour obtenir les tokens
    try:
        session = _sign_in_with_password(request.email, request.password)
    except Exception as e:
        logger.error("Erreur sign-in after register: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Compte créé mais échec de connexion",
        )

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user": {
            "id": user_id,
            "email": email,
            "first_name": request.first_name,
        },
    }


@router.post("/login")
async def login(request: LoginRequest):
    """
    Connecte un utilisateur avec email et mot de passe.
    Retourne les tokens d'accès.
    """
    try:
        session = _sign_in_with_password(request.email, request.password)
    except Exception as e:
        logger.error("Erreur login: %s", e)
        error_str = str(e).lower()
        if "invalid" in error_str or "wrong" in error_str or "credentials" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la connexion",
        )

    user = get_user_by_id(session.user.id) if session.user else None

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user": {
            "id": session.user.id if session.user else None,
            "email": session.user.email if session.user else request.email,
            "first_name": user.get("first_name", "") if user else "",
        },
    }


@router.post("/refresh")
async def refresh(request: RefreshRequest):
    """
    Rafraîchit le token d'accès à l'aide d'un refresh token.
    """
    try:
        session = _refresh_session(request.refresh_token)
    except Exception as e:
        logger.error("Erreur refresh: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide ou expiré",
        )

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user": {
            "id": session.user.id if session.user else None,
            "email": session.user.email if session.user else None,
        },
    }


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """
    Retourne le profil de l'utilisateur connecté.
    """
    # Ne pas exposer le mot de passe haché
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return safe_user
