"""Planner Agent: Breaks down the reverse-engineering task into structured investigation dimensions."""

from typing import Optional
from google import genai
from .models import ResearchPlan, ResearchPlanItem
from .gemini_client import generate_content


PLANNER_SYSTEM_PROMPT = """You are a Principal Software Reverse-Engineering Architect.
Your mission is to take any software tool, SaaS platform, AI agent, protocol, or API, and formulate a rigorous, highly-targeted multi-dimensional research plan to thoroughly reverse engineer its mechanics.

You must design a plan covering these core dimensions:
1. System Architecture & Tech Stack (Frontend, Backend, Databases, Message Brokers, Edge workers, LLM engines)
2. APIs, Protocols & Communication (REST, GraphQL, WebSockets, gRPC, Server-Sent Events, Header conventions, Payload structures)
3. Internal Workflow & Execution Logic (State machines, job queues, algorithms, caching, prompt chains, agentic loops)
4. Data Models & State Persistence (Entities, relationships, session storage, schemas)
5. Reconstruction Blueprint (How a developer can recreate this tool from scratch using modern open-source technologies)

For each dimension, generate highly specific and technical search queries targeting engineering blogs, GitHub teardowns, developer docs, API references, network inspection posts, and open-source equivalents.
"""


def generate_reverse_engineering_plan(
    client: genai.Client,
    tool_name: str,
    mode: str = "Full Reverse Engineering",
    custom_notes: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> ResearchPlan:
    """Generate a structured, editable investigation plan for the target tool."""
    prompt = f"""Target Tool to Reverse Engineer: {tool_name}
Target Analysis Mode: {mode}
Custom Directives / Special Focus: {custom_notes or 'Comprehensive technical breakdown'}

Please generate a detailed, structured research plan with 4 to 6 core investigation dimensions.
Each dimension must contain targeted search queries that will help uncover internal implementation details, network payloads, API structure, and architecture.
"""

    result = generate_content(
        client=client,
        model=model,
        prompt=prompt,
        system_instruction=PLANNER_SYSTEM_PROMPT,
        response_schema=ResearchPlan,
        temperature=0.2,
    )

    if isinstance(result, ResearchPlan):
        return result
    elif isinstance(result, dict):
        return ResearchPlan(**result)
    else:
        # Fallback parsing
        import json
        data = json.loads(str(result))
        return ResearchPlan(**data)
