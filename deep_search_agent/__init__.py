"""Deep Search Agent for Software & Tool Reverse Engineering.
Inspired by Google ADK (Agent Development Kit) deep-search recipe.
"""

from .models import (
    ResearchPlan,
    ResearchPlanItem,
    ResearchFindings,
    Feedback,
    ReverseEngineeringDossier,
)
from .planner import generate_reverse_engineering_plan
from .researcher import execute_research_step
from .evaluator import evaluate_research_findings
from .synthesizer import generate_reverse_engineering_dossier

__all__ = [
    "ResearchPlan",
    "ResearchPlanItem",
    "ResearchFindings",
    "Feedback",
    "ReverseEngineeringDossier",
    "generate_reverse_engineering_plan",
    "execute_research_step",
    "evaluate_research_findings",
    "generate_reverse_engineering_dossier",
]
