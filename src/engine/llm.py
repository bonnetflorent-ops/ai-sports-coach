"""Client LLM avec retry et circuit breaker."""
import asyncio
import logging
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from src.utils.config import settings

logger = logging.getLogger(__name__)

_client = None
_failure_count = 0
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_RESET_SECONDS = 60


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=30.0,
            max_retries=0,
        )
    return _client


async def chat(
    messages: list[dict],
    max_retries: int = 2,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> str:
    global _failure_count

    if _failure_count >= CIRCUIT_BREAKER_THRESHOLD:
        raise RuntimeError(
            f"Circuit breaker ouvert ({_failure_count} échecs récents). "
            f"Réessaie dans {CIRCUIT_RESET_SECONDS}s."
        )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await get_client().chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _failure_count = 0
            return response.choices[0].message.content

        except RateLimitError as e:
            last_error = e
            _failure_count += 1
            wait = 2 ** attempt
            logger.warning(
                f"Rate limit OpenRouter (tentative {attempt+1}/{max_retries+1}), "
                f"attente {wait}s"
            )
            await asyncio.sleep(wait)

        except APITimeoutError as e:
            last_error = e
            _failure_count += 1
            wait = 2 ** attempt
            logger.warning(
                f"Timeout OpenRouter (tentative {attempt+1}/{max_retries+1}), "
                f"attente {wait}s"
            )
            await asyncio.sleep(wait)

        except APIError as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur API OpenRouter: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)

        except Exception as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur inconnue OpenRouter: {e}", exc_info=True)
            raise

    raise RuntimeError(
        f"Échec après {max_retries+1} tentatives. "
        f"Dernière erreur: {last_error}"
    )


async def chat_with_metrics(
    messages: list[dict],
    max_retries: int = 2,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> dict:
    global _failure_count

    if _failure_count >= CIRCUIT_BREAKER_THRESHOLD:
        raise RuntimeError(
            f"Circuit breaker ouvert ({_failure_count} échecs récents). "
            f"Réessaie dans {CIRCUIT_RESET_SECONDS}s."
        )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await get_client().chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            _failure_count = 0
            usage = response.usage
            finish_reason = response.choices[0].finish_reason
            content = response.choices[0].message.content

            # Safety: OpenRouter can return null content even with tokens generated
            if content is None:
                logger.warning(
                    "llm_null_content: tokens_out=%s tokens_in=%s finish_reason=%s — falling back to empty string",
                    usage.completion_tokens if usage else 0,
                    usage.prompt_tokens if usage else 0,
                    finish_reason,
                )
                content = ""

            if finish_reason == "length":
                logger.warning(
                    "llm_truncated: tokens_out=%s tokens_in=%s finish_reason=%s",
                    usage.completion_tokens if usage else 0,
                    usage.prompt_tokens if usage else 0,
                    finish_reason,
                )
            return {
                "content": content,
                "tokens_in": usage.prompt_tokens if usage else 0,
                "tokens_out": usage.completion_tokens if usage else 0,
                "model": response.model,
                "finish_reason": finish_reason,
            }

        except RateLimitError as e:
            last_error = e
            _failure_count += 1
            await asyncio.sleep(2 ** attempt)

        except APITimeoutError as e:
            last_error = e
            _failure_count += 1
            await asyncio.sleep(2 ** attempt)

        except APIError as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur API OpenRouter: {e}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)

        except Exception as e:
            last_error = e
            _failure_count += 1
            logger.error(f"Erreur inconnue OpenRouter: {e}", exc_info=True)
            raise

    raise RuntimeError(
        f"Échec après {max_retries+1} tentatives. "
        f"Dernière erreur: {last_error}"
    )
