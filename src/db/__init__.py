"""
Client Supabase lazy-loadé pour AI Sports Coach.

Deux clients :
- anon : clé publishable, respecte les Row Level Security (RLS)
- admin : clé service_role, bypass RLS, pour opérations backend
"""

from supabase import create_client, Client
from src.utils.config import settings

_anon_client: Client | None = None
_admin_client: Client | None = None


def get_supabase() -> Client:
    """Retourne le client Supabase avec la clé anon (publishable)."""
    global _anon_client
    if _anon_client is None:
        if not settings.supabase_url or not settings.supabase_anon_key:
            raise RuntimeError("SUPABASE_URL et SUPABASE_ANON_KEY sont requis")
        _anon_client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _anon_client


def get_supabase_admin() -> Client:
    """Retourne le client Supabase avec la clé service_role (admin, bypass RLS)."""
    global _admin_client
    if _admin_client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_KEY sont requis")
        _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _admin_client


def check_connection() -> dict:
    """Vérifie que la connexion Supabase fonctionne. Retourne un dict status."""
    try:
        admin = get_supabase_admin()
        # Vérifier que les tables existent
        result = admin.table("users").select("id", count="exact").limit(0).execute()
        return {
            "ok": True,
            "url": settings.supabase_url,
            "users_count": result.count,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
