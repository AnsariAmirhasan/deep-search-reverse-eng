"""Gemini API client and search provider integration."""

import os
import json
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


def generate_content(
    client: genai.Client,
    model: str,
    prompt: str,
    system_instruction: Optional[str] = None,
    use_search_grounding: bool = False,
    response_schema: Optional[Any] = None,
    temperature: float = 0.2,
) -> Any:
    """Unified wrapper around Gemini generate_content supporting grounding and structured schemas."""
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

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    if response_schema:
        try:
            return response.parsed
        except Exception:
            return json.loads(response.text)

    return response
