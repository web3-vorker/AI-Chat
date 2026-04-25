from openai import AsyncOpenAI, APIError, APIConnectionError
import httpx
import logging

from backend.config.config import app_config

logger = logging.getLogger(__name__)


class AiClient:
    def __init__(self, *, model: str | None = None, http_client: httpx.AsyncClient | None = None):
        self._http_client = http_client or httpx.AsyncClient()
        api_key = app_config.openrouter_api_key or "test"
        if not app_config.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY is not set; using a placeholder key (requests will fail in prod).")

        default_headers: dict[str, str] = {}
        if app_config.openrouter_site_url:
            default_headers["HTTP-Referer"] = app_config.openrouter_site_url
        if app_config.openrouter_app_name:
            default_headers["X-Title"] = app_config.openrouter_app_name
        default_headers_param = default_headers or None
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            http_client=self._http_client,
            default_headers=default_headers_param,
        )
        self.model = model or app_config.openrouter_model
    
    async def chat(self, messages: list[dict]) -> str:
        try:
            if not isinstance(messages, list) or not messages:
                raise ValueError("messages must be a non-empty list")
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    raise ValueError(f"messages[{i}] must be a dict with role/content")
                if msg["role"] not in {"system", "user", "assistant"}:
                    raise ValueError(f"messages[{i}].role must be system/user/assistant")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                timeout=30.0
            )
            
            if not response.choices or not response.choices[0].message.content:
                logger.warning("Empty response from OpenRouter")
                raise ValueError("Empty response from AI model")
            
            return response.choices[0].message.content
                
        except APIConnectionError as e:
            logger.error(f"Connection to OpenRouter failed: {e}", exc_info=True)
            raise
        except APIError as e:
            logger.error(f"OpenRouter API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI chat: {e}", exc_info=True)
            raise

    async def aclose(self) -> None:
        await self._http_client.aclose()
