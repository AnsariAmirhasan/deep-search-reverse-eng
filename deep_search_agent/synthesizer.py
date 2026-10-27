"""Synthesizer Agent: Compiles findings into an exhaustive Reverse-Engineering Dossier."""

import json
from google import genai
from .models import ResearchFindings, ReverseEngineeringDossier
from .gemini_client import generate_content

SYNTHESIZER_SYSTEM_PROMPT = """You are a World-Class Principal Software Architect and Reverse-Engineering Lead.
Your goal is to synthesize raw multi-stage research findings into an authoritative, professional, and exhaustively detailed Reverse-Engineering Dossier and Reconstruction Blueprint.

Your output must be organized, rigorous, and directly useful to senior software engineers:
1. Executive Summary: What the tool is, core value proposition, key engineering highlights.
2. Inferred Tech Stack: Categorized map of technologies (Frontend, Backend, DB/Cache, Messaging/Queues, Protocols, AI Models/Runtimes).
3. Architecture Overview: Deep technical narrative of all subsystems and communication boundaries.
4. Mermaid Diagram: A clean, syntactically valid Mermaid flowchart (e.g. `graph TD` or `sequenceDiagram`) illustrating the architecture and data flow.
5. API Specifications: Inferred/documented endpoints, HTTP methods, headers, query parameters, request bodies, and response payloads.
6. Data Models & Storage: Inferred database schema (tables/collections, fields, indexes, relationships).
7. Internal Execution Logic: Step-by-step algorithms, state machines, prompt chaining, or agentic loop patterns used internally.
8. Reconstruction Blueprint: Step-by-step guide with recommended open-source stack, project directory structure, and starter code snippets.
9. Sources Cited: Referenced URLs and docs.
"""


def generate_reverse_engineering_dossier(
    client: genai.Client,
    tool_name: str,
    findings: ResearchFindings,
    model: str = "gemini-3.8-flash",
) -> ReverseEngineeringDossier:
    """Synthesize all research into the structured Reverse-Engineering Dossier."""
    all_findings_text = "\n\n".join(findings.raw_findings)
    sources_summary = "\n".join([
        f"[{src.id}] {src.title} - {src.url}"
        for src in findings.sources.values()
    ])

    prompt = f"""Target Tool to Reverse Engineer: {tool_name}

Research Findings from Deep Investigation:
{all_findings_text}

Grounded Web Sources:
{sources_summary}

Please generate the complete, production-grade ReverseEngineeringDossier.
Ensure the mermaid_diagram is completely valid mermaid syntax (e.g., starts with graph TD or sequenceDiagram) and represents the true data flow.
Make the API specifications and Reconstruction Blueprint concrete with actual code samples and schemas.
"""

    result = generate_content(
        client=client,
        model=model,
        prompt=prompt,
        system_instruction=SYNTHESIZER_SYSTEM_PROMPT,
        response_schema=ReverseEngineeringDossier,
        temperature=0.2,
    )

    if isinstance(result, ReverseEngineeringDossier):
        return result
    elif isinstance(result, dict):
        return ReverseEngineeringDossier(**result)
    else:
        try:
            return ReverseEngineeringDossier(**json.loads(str(result)))
        except Exception:
            # Fallback
            import re
            text = str(result)
            return ReverseEngineeringDossier(
                tool_name=tool_name,
                executive_summary="Summary generated from findings.",
                tech_stack={"General": ["Inferred from deep search"]},
                architecture_overview=text[:2000],
                mermaid_diagram="graph TD\n    Client[Client Browser / Desktop] --> API[API Gateway]\n    API --> Service[Core Engine]\n    Service --> DB[(Database / Cache)]",
                api_specifications="Refer to findings for full endpoint specifications.",
                data_models_and_storage="Refer to architecture section.",
                workflow_and_algorithms="Iterative execution pipeline.",
                reconstruction_blueprint="Use standard FastAPI + React/Streamlit architecture.",
                sources_cited=[{"title": s.title, "url": s.url} for s in findings.sources.values()],
            )
