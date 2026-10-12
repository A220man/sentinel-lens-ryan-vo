"""Tests for multi-provider LLM adapters, mocking network providers, and error redaction."""

from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.core.config import settings
from app.services.llm_adapters import LLMAdvisoryService, LLMAdapterError


@pytest.mark.anyio
async def test_offline_fallback_when_no_api_key():
    service = LLMAdvisoryService()
    with patch.object(settings, "llm_api_key", ""):
        result = await service.generate_explanation(
            prompt="Why did assert fail?",
            context={"selector": "#btn-test", "status": "failed"},
        )
        assert result["advisory"] is True
        assert result["provider"] == "offline-heuristic"
        assert "Deterministic offline analysis" in result["explanation"]


@pytest.mark.anyio
async def test_openai_adapter_mocked():
    service = LLMAdvisoryService()
    mock_response = httpx.Response(
        200,
        json={
            "choices": [
                {"message": {"content": "The element was not yet rendered into the accessibility tree."}}
            ]
        },
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    with patch.object(settings, "llm_api_key", "test-key-mock"), \
         patch.object(settings, "llm_provider", "openai-compatible"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await service.generate_explanation("Analyze failure", {"step": 1})
        assert result["provider"] == "openai-compatible"
        assert "not yet rendered" in result["explanation"]


@pytest.mark.anyio
async def test_anthropic_adapter_mocked():
    service = LLMAdvisoryService()
    mock_response = httpx.Response(
        200,
        json={"content": [{"text": "Accessibility role mismatch detected."}]},
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )

    with patch.object(settings, "llm_api_key", "test-key-mock"), \
         patch.object(settings, "llm_provider", "anthropic"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await service.generate_explanation("Analyze failure", {"step": 2})
        assert result["provider"] == "anthropic"
        assert "role mismatch" in result["explanation"]


@pytest.mark.anyio
async def test_gemini_adapter_mocked():
    service = LLMAdvisoryService()
    mock_response = httpx.Response(
        200,
        json={
            "candidates": [
                {"content": {"parts": [{"text": "DOM hierarchy modified during click animation."}]}}
            ]
        },
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini:generateContent"),
    )

    with patch.object(settings, "llm_api_key", "test-key-mock"), \
         patch.object(settings, "llm_provider", "gemini"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await service.generate_explanation("Analyze failure", {"step": 3})
        assert result["provider"] == "gemini"
        assert "DOM hierarchy modified" in result["explanation"]


@pytest.mark.anyio
async def test_adapter_error_redaction():
    service = LLMAdvisoryService()
    mock_response = httpx.Response(
        500,
        text="Internal Server Error: Sensitive internal state",
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
    )

    with patch.object(settings, "llm_api_key", "test-key-mock"), \
         patch.object(settings, "llm_provider", "openai-compatible"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(LLMAdapterError) as exc_info:
            await service.generate_explanation("Prompt", {"secret_token": "secret123"})
        assert "500" in str(exc_info.value)
