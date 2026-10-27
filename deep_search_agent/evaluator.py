"""Evaluator Agent: Reflects on accumulated findings and tests for technical completeness."""

import json
from google import genai
from .models import Feedback, ResearchFindings
from .gemini_client import generate_content

EVALUATOR_SYSTEM_PROMPT = """You are an exacting Technical Reviewer & Systems Architect evaluating a reverse-engineering investigation.
Your mission is to evaluate whether the gathered research is technically rigorous and complete enough to produce a complete Reverse-Engineering Dossier and Open-Source Clone Blueprint.

Evaluation criteria:
1. Tech Stack Specificity: Are actual frameworks, libraries, protocols, or infrastructure components identified (rather than generic descriptions)?
2. API & Data Flow: Are endpoints, RPC calls, WebSocket events, or payload shapes identified or clearly inferred?
3. Architecture & Mechanics: Is it clear how user requests flow through the system from ingress to backend/agents to storage?
4. Rebuild Feasibility: Does an engineer have enough concrete direction to replicate this tool?

If critical technical gaps exist (e.g. unknown communication protocol, unclear data model, missing auth pattern), grade MUST be 'fail' with 2 to 3 targeted follow-up queries.
If the information is solid and actionable, grade MUST be 'pass' with empty follow_up_queries.
"""


def evaluate_research_findings(
    client: genai.Client,
    tool_name: str,
    findings: ResearchFindings,
    model: str = "gemini-2.5-flash",
) -> Feedback:
    """Evaluate gathered findings and determine if reflection/follow-up is needed."""
    compiled_findings = "\n\n".join(findings.raw_findings[-4:])  # most recent findings

    prompt = f"""Target Tool: {tool_name}
Accumulated Findings Summary:
{compiled_findings}

Total Sources Gathered: {len(findings.sources)}

Assess whether these findings provide sufficient technical depth to reverse engineer the system architecture, APIs, data flows, and code reconstruction blueprint.
"""

    result = generate_content(
        client=client,
        model=model,
        prompt=prompt,
        system_instruction=EVALUATOR_SYSTEM_PROMPT,
        response_schema=Feedback,
        temperature=0.1,
    )

    if isinstance(result, Feedback):
        return result
    elif isinstance(result, dict):
        return Feedback(**result)
    else:
        try:
            return Feedback(**json.loads(str(result)))
        except Exception:
            return Feedback(grade="pass", comment="Sufficient research gathered.", follow_up_queries=[])
