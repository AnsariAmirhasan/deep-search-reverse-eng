"""DeepSearch Reverse-Engineering Agent UI.
Built with Streamlit & inspired by Google ADK deep-search recipe.
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from deep_search_agent.models import (
    ResearchPlan,
    ResearchPlanItem,
    ResearchFindings,
    Feedback,
    ReverseEngineeringDossier,
)
from deep_search_agent.gemini_client import get_gemini_client
from deep_search_agent.planner import generate_reverse_engineering_plan
from deep_search_agent.researcher import execute_research_step
from deep_search_agent.evaluator import evaluate_research_findings
from deep_search_agent.synthesizer import generate_reverse_engineering_dossier
from deep_search_agent.presets import PRESET_TOOLS

# Configure page
st.set_page_config(
    page_title="DeepSearch Tool Reverse-Engineer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for high-end look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4285F4, #34A853, #FBBC05, #EA4335);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #718096;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #2D3748;
        color: #ED8936;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "plan" not in st.session_state:
    st.session_state.plan = None
if "findings" not in st.session_state:
    st.session_state.findings = None
if "dossier" not in st.session_state:
    st.session_state.dossier = None
if "status_logs" not in st.session_state:
    st.session_state.status_logs = []

# Sidebar Controls
st.sidebar.markdown("### ⚙️ Settings & Configuration")

env_api_key = os.getenv("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=env_api_key,
    type="password",
    help="Enter your Google AI Studio or Vertex AI Gemini API Key. Can also be set in .env as GEMINI_API_KEY.",
)

model_choice = st.sidebar.selectbox(
    "Gemini Model",
    ["gemini-2.5-flash", "gemini-2.5-pro"],
    index=0,
    help="gemini-2.5-flash is fast with search grounding. gemini-2.5-pro provides deeper synthesis.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 Quick Presets")
preset_name = st.sidebar.selectbox(
    "Choose a preset target or Custom",
    ["-- Custom Target --"] + list(PRESET_TOOLS.keys()),
)

default_tool_name = ""
default_mode = "Full Reverse Engineering"
default_notes = ""

if preset_name != "-- Custom Target --":
    preset_data = PRESET_TOOLS[preset_name]
    default_tool_name = preset_data["name"]
    default_mode = preset_data["mode"]
    default_notes = preset_data["notes"]

st.sidebar.markdown("---")
st.sidebar.markdown("""
**About this Agent:**
- 🧠 **ADK Pattern:** Planner → Researcher → Evaluator → Synthesizer.
- 🔄 **Human-in-the-Loop:** Inspect and customize the research plan before execution.
- 🎯 **Target:** Extract internal APIs, protocols, state machines, and code reconstruction blueprints.
""")

# Main Header
st.markdown('<div class="main-header">🔬 DeepSearch Reverse-Engineering Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous multi-agent intelligence platform for reverse engineering software tools, APIs, protocols, and system architectures.</div>', unsafe_allow_html=True)

# Target Definition Form
with st.container():
    col1, col2 = st.columns([3, 2])
    with col1:
        tool_input = st.text_input(
            "Target Tool / Software / Product to Reverse Engineer",
            value=default_tool_name,
            placeholder="e.g. Cursor AI Editor, Perplexity Pro Search, v0.dev, Supabase Realtime, Stripe Checkout",
        )
    with col2:
        mode_options = [
            "Full Reverse Engineering Dossier",
            "API & Protocol Spec Extraction",
            "Architecture & Data Flow Teardown",
            "Open-Source Clone Blueprint",
        ]
        mode_index = 0
        if default_mode in mode_options:
            mode_index = mode_options.index(default_mode)
        mode_input = st.selectbox("Analysis Focus", mode_options, index=mode_index)

    notes_input = st.text_area(
        "Custom Directives / Special Points of Interest (Optional)",
        value=default_notes,
        placeholder="e.g. Focus on internal WebSocket payloads, cache invalidation strategy, prompt pipeline, or auth tokens.",
        height=70,
    )

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    generate_plan_btn = st.button("📋 1. Generate Plan", use_container_width=True, type="primary")
with col_btn2:
    if st.session_state.plan:
        st.caption(f"Plan active for: **{st.session_state.plan.tool_name}** ({len(st.session_state.plan.items)} dimensions)")

# Step 1: Generate Plan
if generate_plan_btn:
    if not api_key:
        st.error("Please provide a Gemini API Key in the sidebar or in your .env file.")
    elif not tool_input.strip():
        st.error("Please enter a target tool or software to reverse engineer.")
    else:
        with st.spinner("🤖 Planner Agent analyzing tool scope and formulating reverse-engineering dimensions..."):
            try:
                client = get_gemini_client(api_key=api_key)
                plan = generate_reverse_engineering_plan(
                    client=client,
                    tool_name=tool_input.strip(),
                    mode=mode_input,
                    custom_notes=notes_input.strip() or None,
                    model=model_choice,
                )
                st.session_state.plan = plan
                st.session_state.findings = None
                st.session_state.dossier = None
                st.success("✅ Reverse-Engineering Plan Generated! Review and customize below.")
            except Exception as e:
                st.error(f"Error generating plan: {e}")

# Step 2: Human-in-the-Loop Plan Review & Execution
if st.session_state.plan:
    st.markdown("---")
    st.markdown("### 📝 Step 2: Review & Approve Investigation Plan (Human-in-the-Loop)")
    st.info(f"Target: **{st.session_state.plan.tool_name}** — {st.session_state.plan.summary}")

    # Editable display of plan dimensions
    items_to_run = []
    for idx, item in enumerate(st.session_state.plan.items):
        with st.expander(f"Dimension {idx+1}: {item.title} [{item.focus_area}]", expanded=(idx < 2)):
            include = st.checkbox("Include in Deep Research", value=True, key=f"include_{item.id}")
            desc = st.text_area("Description / Objectives", value=item.description, key=f"desc_{item.id}", height=70)
            queries_str = st.text_area(
                "Target Search Queries (one per line)",
                value="\n".join(item.target_queries),
                key=f"queries_{item.id}",
                height=80,
            )
            if include:
                updated_item = ResearchPlanItem(
                    id=item.id,
                    title=item.title,
                    focus_area=item.focus_area,
                    description=desc,
                    target_queries=[q.strip() for q in queries_str.split("\n") if q.strip()],
                )
                items_to_run.append(updated_item)

    run_col1, run_col2 = st.columns([2, 3])
    with run_col1:
        start_research_btn = st.button("⚡ 2. Approve Plan & Start Deep Research", type="primary", use_container_width=True)

    if start_research_btn:
        if not api_key:
            st.error("Please provide a Gemini API Key in the sidebar.")
        elif not items_to_run:
            st.warning("Please check at least one dimension to investigate.")
        else:
            client = get_gemini_client(api_key=api_key)
            findings = ResearchFindings(tool_name=st.session_state.plan.tool_name)

            progress_bar = st.progress(0.0)
            status_box = st.empty()
            logs = []

            def log_msg(msg: str):
                logs.append(msg)
                status_box.markdown("\n\n".join(logs[-4:]))

            # Loop through plan items
            total_items = len(items_to_run)
            for i, plan_item in enumerate(items_to_run):
                progress_bar.progress((i) / (total_items + 2))
                execute_research_step(
                    client=client,
                    tool_name=st.session_state.plan.tool_name,
                    plan_item=plan_item,
                    findings=findings,
                    model=model_choice,
                    progress_callback=log_msg,
                )

            # Evaluator / Reflection Loop
            progress_bar.progress((total_items) / (total_items + 2))
            log_msg("🧐 **Evaluator Agent** critiquing findings and checking for technical completeness...")
            feedback = evaluate_research_findings(
                client=client,
                tool_name=st.session_state.plan.tool_name,
                findings=findings,
                model=model_choice,
            )

            log_msg(f"Evaluator Verdict: **{feedback.grade.upper()}** - {feedback.comment}")

            # If fail and follow-up queries provided, execute 1 bonus round
            if feedback.grade == "fail" and feedback.follow_up_queries:
                log_msg(f"🔄 Executing reflection follow-up queries: {feedback.follow_up_queries[:2]}")
                followup_item = ResearchPlanItem(
                    id="followup-dim",
                    title="Reflection Gap Resolution",
                    focus_area="api_protocols",
                    description="Filling missing architectural details identified by Evaluator agent.",
                    target_queries=feedback.follow_up_queries[:3],
                )
                execute_research_step(
                    client=client,
                    tool_name=st.session_state.plan.tool_name,
                    plan_item=followup_item,
                    findings=findings,
                    model=model_choice,
                    progress_callback=log_msg,
                )

            # Synthesizer
            progress_bar.progress((total_items + 1) / (total_items + 2))
            log_msg("🏛️ **Synthesizer Agent** constructing Reverse-Engineering Dossier and Reconstruction Blueprint...")

            dossier = generate_reverse_engineering_dossier(
                client=client,
                tool_name=st.session_state.plan.tool_name,
                findings=findings,
                model=model_choice,
            )

            progress_bar.progress(1.0)
            st.session_state.findings = findings
            st.session_state.dossier = dossier
            st.success("🎉 Deep Reverse-Engineering Complete! Dossier generated below.")


# Step 3: Interactive Results Dossier
if st.session_state.dossier:
    dossier: ReverseEngineeringDossier = st.session_state.dossier
    st.markdown("---")
    st.markdown(f"## 📊 Reverse-Engineering Dossier: `{dossier.tool_name}`")

    # Export toolbar
    exp_col1, exp_col2, exp_col3 = st.columns([2, 2, 2])

    full_markdown_report = f"""# Reverse-Engineering Dossier: {dossier.tool_name}

## 1. Executive Summary
{dossier.executive_summary}

## 2. Inferred Tech Stack
{json.dumps(dossier.tech_stack, indent=2)}

## 3. System Architecture
{dossier.architecture_overview}

```mermaid
{dossier.mermaid_diagram}
```

## 4. API & Protocol Specifications
{dossier.api_specifications}

## 5. Data Models & State Persistence
{dossier.data_models_and_storage}

## 6. Internal Workflow & Execution Logic
{dossier.workflow_and_algorithms}

## 7. Open-Source Reconstruction Blueprint
{dossier.reconstruction_blueprint}

## 8. Sources & Grounded References
{json.dumps(dossier.sources_cited, indent=2)}
"""

    with exp_col1:
        st.download_button(
            "📥 Download Dossier (.md)",
            data=full_markdown_report,
            file_name=f"{dossier.tool_name.lower().replace(' ', '_')}_reverse_engineering_dossier.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with exp_col2:
        st.download_button(
            "📥 Download Structured JSON",
            data=json.dumps(dossier.model_dump(), indent=2),
            file_name=f"{dossier.tool_name.lower().replace(' ', '_')}_spec.json",
            mime="application/json",
            use_container_width=True,
        )

    # Tabs for structured viewing
    tab_arch, tab_api, tab_logic, tab_rebuild, tab_sources = st.tabs([
        "🏛️ Architecture & Stack",
        "🔌 APIs & Protocols",
        "⚙️ Workflows & Logic",
        "🛠️ Clone Blueprint",
        "🌐 Grounded Sources",
    ])

    with tab_arch:
        st.markdown("### Executive Summary")
        st.markdown(dossier.executive_summary)

        st.markdown("### Inferred Tech Stack")
        if isinstance(dossier.tech_stack, dict):
            for category, items in dossier.tech_stack.items():
                badges_html = " ".join([f'<span class="badge">{item}</span>' for item in items])
                st.markdown(f"**{category}:** {badges_html}", unsafe_allow_html=True)

        st.markdown("### Architecture Overview")
        st.markdown(dossier.architecture_overview)

        st.markdown("### Architecture & Data Flow Diagram")
        st.code(dossier.mermaid_diagram, language="mermaid")

    with tab_api:
        st.markdown("### API & Protocol Specifications")
        st.markdown(dossier.api_specifications)

        st.markdown("### Inferred Data Models & Schemas")
        st.markdown(dossier.data_models_and_storage)

    with tab_logic:
        st.markdown("### Internal Workflows & Execution Logic")
        st.markdown(dossier.workflow_and_algorithms)

    with tab_rebuild:
        st.markdown("### Open-Source Reconstruction Blueprint")
        st.info("Follow this blueprint to reconstruct an open-source equivalent or alternative of this tool.")
        st.markdown(dossier.reconstruction_blueprint)

    with tab_sources:
        st.markdown("### Grounded Web Sources")
        if st.session_state.findings and st.session_state.findings.sources:
            for src_id, src in st.session_state.findings.sources.items():
                st.markdown(f"- **[{src_id}] [{src.title}]({src.url})** (`{src.domain}`)")
        elif dossier.sources_cited:
            for s in dossier.sources_cited:
                st.markdown(f"- [{s.get('title', 'Source')}]({s.get('url', '#')})")
        else:
            st.caption("No external sources recorded.")
