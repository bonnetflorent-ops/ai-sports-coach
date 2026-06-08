import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # LLM — compatible avec OpenRouter ET DeepSeek direct
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    llm_base_url: str = os.getenv("LLM_BASE_URL", os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"))
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")  # backward compat
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")  # backward compat
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    selector_model: str = os.getenv("SELECTOR_MODEL", "deepseek-chat")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    vapid_private_key: str = os.getenv("VAPID_PRIVATE_KEY", "")
    vapid_public_key: str = os.getenv("VAPID_PUBLIC_KEY", "")
    vapid_subject: str = os.getenv("VAPID_SUBJECT", "mailto:contact@ai-sports-coach.com")


settings = Settings()
