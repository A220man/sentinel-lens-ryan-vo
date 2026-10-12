"""Multi-provider LLM adapter for advisory test failure explanations and locator suggestions."""

from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.core.redaction import default_redactor


class LLMAdapterError(RuntimeError):
    """Exception raised when an upstream LLM provider fails."""
    pass


class LLMAdvisoryService:
    """Dispatches test context to configurable LLM providers; strictly server-side and opt-in."""

    def __init__(self):
        self.timeout = settings.llm_timeout_seconds

    def is_configured(self) -> bool:
        """Determines if an LLM key is configured on the server."""
        return bool(settings.llm_api_key and settings.llm_api_key.strip())

    async def generate_explanation(
        self,
        prompt: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Queries the configured provider adapter with redacted inputs and bounded timeout."""
        if not self.is_configured():
            return {
                "advisory": True,
                "provider": "offline-heuristic",
                "explanation": (
                    "Deterministic offline analysis: Element assertion failed due to missing accessibility "
                    "name or changed DOM hierarchy. No server-side LLM_API_KEY configured."
                ),
                "suggestion": "Verify element testId or role attribute in the component template.",
            }

        sanitized_context = default_redactor.redact_data(context)
        system_instruction = (
            "You are Sentinel Lens Test Advisory Engine. Analyze the failed test step and DOM context. "
            "Provide a concise, grounded explanation of the failure and actionable fix."
        )
        full_content = f"{prompt}\n\nContext:\n{sanitized_context}"

        provider = settings.llm_provider.lower().strip()
        try:
            if provider == "anthropic":
                return await self._call_anthropic(system_instruction, full_content)
            elif provider == "gemini":
                return await self._call_gemini(system_instruction, full_content)
            else:
                # Default: openai-compatible (covers OpenAI, Ollama, LiteLLM, OpenRouter)
                return await self._call_openai_compatible(system_instruction, full_content)
        except Exception as exc:
            # Redact errors to prevent key leakage in exception strings
            safe_error = default_redactor.redact_text(str(exc))
            raise LLMAdapterError(f"LLM provider '{provider}' error: {safe_error}") from None

    async def _call_openai_compatible(self, system: str, content: str) -> Dict[str, Any]:
        base_url = settings.llm_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "temperature": 0.2,
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise LLMAdapterError(f"OpenAI-compatible endpoint returned HTTP {resp.status_code}")
            data = resp.json()
            message_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "advisory": True,
                "provider": "openai-compatible",
                "model": settings.llm_model,
                "explanation": message_text,
                "suggestion": "Check locator selector specificity and wait conditions.",
            }

    async def _call_anthropic(self, system: str, content: str) -> Dict[str, Any]:
        base_url = settings.llm_base_url.rstrip("/") if settings.llm_base_url != "https://api.openai.com/v1" else "https://api.anthropic.com/v1"
        url = f"{base_url}/messages"
        headers = {
            "x-api-key": settings.llm_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model if "claude" in settings.llm_model else "claude-3-haiku-20240307",
            "system": system,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 400,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise LLMAdapterError(f"Anthropic endpoint returned HTTP {resp.status_code}")
            data = resp.json()
            message_text = data.get("content", [{}])[0].get("text", "")
            return {
                "advisory": True,
                "provider": "anthropic",
                "model": settings.llm_model,
                "explanation": message_text,
                "suggestion": "Check accessibility tree role and name properties.",
            }

    async def _call_gemini(self, system: str, content: str) -> Dict[str, Any]:
        base_url = settings.llm_base_url.rstrip("/") if settings.llm_base_url != "https://api.openai.com/v1" else "https://generativelanguage.googleapis.com/v1beta"
        model_name = settings.llm_model if "gemini" in settings.llm_model else "gemini-1.5-flash"
        url = f"{base_url}/models/{model_name}:generateContent?key={settings.llm_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\n{content}"}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise LLMAdapterError(f"Gemini endpoint returned HTTP {resp.status_code}")
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            return {
                "advisory": True,
                "provider": "gemini",
                "model": model_name,
                "explanation": text,
                "suggestion": "Verify accessibility tree matching criteria.",
            }


llm_advisory_service = LLMAdvisoryService()
