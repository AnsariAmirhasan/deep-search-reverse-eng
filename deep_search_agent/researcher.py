"""Researcher Agent: Executes searches, gathers sources, and extracts internal technical details."""

import logging
from typing import Dict, Any, List, Callable, Optional
from google import genai
from .models import ResearchPlanItem, ResearchFindings, SearchSource
from .gemini_client import generate_content, search_web_fallback

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = """You are an elite Security & Software Reverse-Engineering Intelligence Agent.
Your job is to examine technical search results and engineering details about a target tool, and extract concrete, actionable implementation details.

Focus on discovering:
- Exact tech stack, framework names, protocol types (HTTP/2, gRPC, WebSocket, SSE)
- API endpoint paths, HTTP verbs, typical request/response parameters, headers
- Internal architecture components (e.g. gateway, ingestion pipeline, workers, message queues)
- State management and database schemas
- Core algorithms, prompt structures, or agent loops
- Open source alternatives and cloning recipes

Provide precise, structured, technical notes. Avoid vague fluff. Mention specific libraries, formats, and design patterns.
"""


def execute_research_step(
    client: genai.Client,
    tool_name: str,
    plan_item: ResearchPlanItem,
    findings: ResearchFindings,
    model: str = "gemini-2.5-flash",
    progress_callback: Optional[Callable[[str], None]] = None,
) -> None:
    """Execute research on an individual plan dimension using search grounding and extraction."""
    if progress_callback:
        progress_callback(f"🔍 Investigating: **{plan_item.title}** ({plan_item.focus_area})...")

    # Combine queries for this dimension
    query_text = " OR ".join(plan_item.target_queries[:3])
    prompt = f"""Target Tool: {tool_name}
Investigation Dimension: {plan_item.title}
Focus Area: {plan_item.focus_area}
Description: {plan_item.description}
Key Target Queries:
{chr(10).join(f"- {q}" for q in plan_item.target_queries)}

Perform a deep technical inquiry using Google Search Grounding to uncover real architecture details, API specs, protocols, GitHub discussions, tech stack, and internal workings.
Summarize the concrete reverse-engineering findings with precise technical details.
"""

    sources_found: List[Dict[str, str]] = []
    response_text = ""

    try:
        # Attempt search grounding with Gemini
        response = generate_content(
            client=client,
            model=model,
            prompt=prompt,
            system_instruction=RESEARCHER_SYSTEM_PROMPT,
            use_search_grounding=True,
            temperature=0.2,
        )

        response_text = response.text or ""

        # Extract grounding metadata if available (standard in google-genai)
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            grounding_metadata = getattr(candidate, "grounding_metadata", None)
            if grounding_metadata:
                chunks = getattr(grounding_metadata, "grounding_chunks", []) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    if web:
                        uri = getattr(web, "uri", "")
                        title = getattr(web, "title", uri)
                        domain = getattr(web, "domain", "")
                        if uri:
                            sources_found.append({
                                "url": uri,
                                "title": title,
                                "domain": domain,
                            })
    except Exception as e:
        logger.warning(f"Search grounding exception: {e}. Falling back to search fallback...")
        if progress_callback:
            progress_callback(f"⚠️ Search grounding notice ({e}), running web query fallback...")

        # Fallback using DuckDuckGo
        fallback_results = []
        for q in plan_item.target_queries[:2]:
            fallback_results.extend(search_web_fallback(f"{tool_name} {q}", max_results=3))

        fallback_context = "\n\n".join(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['body']}"
            for r in fallback_results
        )

        for r in fallback_results:
            sources_found.append({
                "url": r["url"],
                "title": r["title"],
                "domain": r["url"].split("/")[2] if "/" in r["url"] else "",
            })

        fallback_prompt = f"""Target Tool: {tool_name}
Dimension: {plan_item.title}
Web Context:
{fallback_context}

Analyze this context and extract all technical reverse-engineering insights (tech stack, APIs, architecture, workflows).
"""
        resp = generate_content(
            client=client,
            model=model,
            prompt=fallback_prompt,
            system_instruction=RESEARCHER_SYSTEM_PROMPT,
            use_search_grounding=False,
            temperature=0.2,
        )
        response_text = resp.text or ""

    # Record sources
    for s in sources_found:
        url = s.get("url", "")
        if url and url not in [src.url for src in findings.sources.values()]:
            src_id = f"src-{len(findings.sources) + 1}"
            findings.sources[src_id] = SearchSource(
                id=src_id,
                title=s.get("title", url),
                url=url,
                domain=s.get("domain", ""),
            )

    findings.raw_findings.append(
        f"### {plan_item.title} ({plan_item.focus_area})\n{response_text}"
    )

    if progress_callback:
        progress_callback(f"✅ Completed investigation for: **{plan_item.title}** (Found {len(sources_found)} sources).")
