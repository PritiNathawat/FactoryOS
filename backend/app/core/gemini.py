"""
FactoryOS Gemini Client
========================
Async-native wrapper around the Google Gemini API (google-genai SDK).

Design decisions:
  - Uses google-genai's native async API — no thread executor needed
  - Supports schema-constrained JSON output for deterministic structured responses
  - Mock mode when GEMINI_API_KEY is not configured
  - Shared singleton via get_gemini_client() — one connection per process

ADK Note:
  The google-adk framework builds on google-genai internally.
  When migrating to ADK, replace direct client calls with Agent.run()
  and this module becomes the underlying tool configuration.

Usage:
    client = get_gemini_client()
    result = await client.generate_json(
        user_prompt="Analyze this incident: ...",
        system_instruction="You are the Maintenance Agent...",
    )
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional, Type

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Async Gemini API client for all FactoryOS agents.

    Wraps google-genai's async API with:
    - Structured JSON generation (schema-constrained)
    - Mock mode (no API key required for testing)
    - Structured logging for observability
    """

    def __init__(self) -> None:
        self._model = settings.gemini_model
        self._temperature = settings.gemini_temperature
        self._max_tokens = settings.gemini_max_tokens
        self._mock_mode = not bool(settings.gemini_api_key)

        if self._mock_mode:
            logger.warning(
                "Gemini client initialized in MOCK MODE. "
                "Set GEMINI_API_KEY in .env to enable real AI responses."
            )
        else:
            # Lazy import — avoids ImportError if google-genai is not installed
            # during unit tests that mock the client
            from google import genai as _genai  # noqa: F401
            self._genai_client = _genai.Client(api_key=settings.gemini_api_key)
            logger.info(
                "Gemini client initialized",
                extra={"model": self._model},
            )

    @property
    def is_mock(self) -> bool:
        return self._mock_mode

    async def generate_json(
        self,
        user_prompt: str,
        system_instruction: str,
        response_schema: Optional[Type[BaseModel]] = None,
        temperature: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response from Gemini.

        When GEMINI_API_KEY is not configured, returns a mock response
        that signals mock mode to the caller.

        Args:
            user_prompt: The main content prompt (includes incident data + tool results)
            system_instruction: The agent's persona and expertise instructions
            response_schema: Optional Pydantic model — enables schema-constrained generation
            temperature: Override the default temperature for this call

        Returns:
            Parsed JSON dict — always valid (raises on parse failure)
        """
        if self._mock_mode:
            return self._generate_mock_response(user_prompt, system_instruction)

        start = time.monotonic()

        try:
            from google.genai import types

            config_kwargs: dict[str, Any] = {
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": temperature or self._temperature,
                "max_output_tokens": self._max_tokens,
            }

            # Schema-constrained generation guarantees output matches our Pydantic models.
            # Without this, we rely on prompt instructions alone (less reliable).
            if response_schema is not None:
                config_kwargs["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_kwargs)

            response = await self._genai_client.aio.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=config,
            )

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "Gemini API call completed",
                extra={
                    "model": self._model,
                    "elapsed_ms": elapsed_ms,
                    "schema_constrained": response_schema is not None,
                    "prompt_length": len(user_prompt),
                },
            )

            return json.loads(response.text)

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini response as JSON", exc_info=exc)
            raise ValueError(f"Gemini returned non-JSON output: {exc}") from exc
        except Exception as exc:
            logger.error("Gemini API call failed", exc_info=exc)
            raise

    def _generate_mock_response(
        self,
        user_prompt: str,
        system_instruction: str,
    ) -> dict[str, Any]:
        """
        Returns a plausible mock response when no API key is configured.

        The mock response signals MOCK status so the platform can indicate
        this in the OrchestratorResult. This is intentional — the system
        never silently pretends to have called Gemini.
        """
        # Extract agent name from system instruction for mock labeling
        agent_name = "unknown"
        for keyword in ["Maintenance", "Inventory", "Production", "Cost", "Reporting", "Manager"]:
            if keyword in system_instruction:
                agent_name = keyword.lower()
                break

        return {
            "agent_name": agent_name,
            "status": "mock",
            "confidence": 0.75,
            "reasoning": (
                f"[MOCK MODE] This is a simulated response from the {agent_name} agent. "
                "Configure GEMINI_API_KEY in .env for real AI analysis."
            ),
            "recommendation": (
                "Inspect Machine M-12 bearings immediately. "
                "Schedule replacement within 4 hours to prevent further damage."
            ),
            "tools_used": [],
            "data": {
                "mock": True,
                "note": "Configure GEMINI_API_KEY for real AI-powered analysis.",
            },
        }


# ─── Module-level Singleton ───────────────────────────────────

_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Return the shared GeminiClient singleton.

    Creating one client per process is the correct pattern for google-genai.
    The client manages its own connection pool internally.
    """
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
