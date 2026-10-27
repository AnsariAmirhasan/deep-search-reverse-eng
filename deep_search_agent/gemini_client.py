"""Gemini API client and search provider integration."""

import os
import time
import json
import random
import logging
from typing import Optional, Any, Dict, List
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """Initialize Google GenAI client from provided key or environment variable."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Gemini API Key is required. Please set GEMINI_API_KEY environment variable or provide it in the UI."
        )
    return genai.Client(api_key=key)


def search_web_fallback(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Fallback search using DuckDuckGo if search grounding is offline or needed for supplementary discovery."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "body": r.get("body", ""),
                })
        return results
    except Exception as e:
        logger.warning(f"Fallback search error: {e}")
        return []


MODEL_ALIASES = {
    "gemini-2.5-flash": "gemini-3.8-flash",
    "gemini-2.5-pro": "gemini-3.1-pro-preview",
    "gemini-2.0-flash": "gemini-3.8-flash",
    "gemini-1.5-flash": "gemini-3.8-flash",
    "gemini-1.5-pro": "gemini-3.1-pro-preview",
}

FAILOVER_MODELS = {
    "gemini-3.8-flash": "gemini-3.5-flash-lite",
    "gemini-3.1-pro-preview": "gemini-3.8-flash",
    "gemini-3.5-flash-lite": "gemini-3.8-flash",
}


def generate_content(
    client: genai.Client,
    model: str,
    prompt: str,
    system_instruction: Optional[str] = None,
    use_search_grounding: bool = False,
    response_schema: Optional[Any] = None,
    temperature: float = 0.2,
    max_retries: int = 3,
) -> Any:
    """Unified wrapper around Gemini generate_content supporting retries, failovers, grounding and schemas."""
    # Automatically resolve legacy model strings to latest Gemini 3.8 models
    actual_model = MODEL_ALIASES.get(model, model)

    config_params: Dict[str, Any] = {
        "temperature": temperature,
    }

    if system_instruction:
        config_params["system_instruction"] = system_instruction

    if use_search_grounding:
        # Enable Google Search Grounding tool
        config_params["tools"] = [{"google_search": {}}]

    if response_schema:
        config_params["response_mime_type"] = "application/json"
        config_params["response_schema"] = response_schema

    config = types.GenerateContentConfig(**config_params)

    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=actual_model,
                contents=prompt,
                config=config,
            )

            if response_schema:
                try:
                    return response.parsed
                except Exception:
                    return json.loads(response.text)

            return response
        except Exception as e:
            err_msg = str(e)
            last_exception = e
            # Check for transient errors (503 UNAVAILABLE or 429 RESOURCE_EXHAUSTED)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                backoff_delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                logger.warning(
                    f"Transient API error ({err_msg}) on {actual_model}. Retrying in {backoff_delay:.2f}s (Attempt {attempt+1}/{max_retries})..."
                )
                time.sleep(backoff_delay)
                # On the last retry, attempt failover model if available
                if attempt == max_retries - 2:
                    fallback = FAILOVER_MODELS.get(actual_model)
                    if fallback and fallback != actual_model:
                        logger.info(f"Failing over from {actual_model} to {fallback} due to high traffic.")
                        actual_model = fallback
            else:
                # Non-transient error, raise immediately
                raise e

    # If all retries exhausted, raise last exception
    if last_exception:
        raise last_exception
