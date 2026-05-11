from openai import AsyncOpenAI
from src.utils.config import settings

_client = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


async def chat(messages: list[dict]) -> str:
    """Envoie une conversation à DeepSeek, retourne la réponse texte."""
    response = await get_client().chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )
    return response.choices[0].message.content
