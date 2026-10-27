"""Pre-configured reverse engineering targets and templates."""

PRESET_TOOLS = {
    "Cursor AI Editor (Agent & Indexing Engine)": {
        "name": "Cursor AI Editor (Anysphere)",
        "mode": "Full Reverse Engineering",
        "notes": "Focus on: Codebase semantic indexing (shadow workspace, embeddings, merkle tree sync), Composer agent loop, diff generation engine, and how it intercepts VS Code language server protocols.",
    },
    "Perplexity AI (Deep Search & Grounding Engine)": {
        "name": "Perplexity AI Pro Search",
        "mode": "Architecture & Workflow Teardown",
        "notes": "Focus on: Query fanout & expansion, multi-source scraping/SERP orchestration, reranker model integration, inline citation synthesis, and streaming SSE protocol.",
    },
    "v0.dev by Vercel (Generative UI System)": {
        "name": "v0.dev Generative UI Engine",
        "mode": "Open-Source Clone Blueprint",
        "notes": "Focus on: React/Tailwind/Lucide AST generation, sandboxed live preview runtime (Sandpack / WebContainers), incremental component patch streaming, and prompt design.",
    },
    "Stripe Checkout & Webhook Pipeline": {
        "name": "Stripe Hosted Checkout & Webhooks",
        "mode": "API & Protocol Spec Extraction",
        "notes": "Focus on: Hosted checkout session creation, cryptographic signature verification (HMAC-SHA256), idempotent request handling, retry exponential backoff queues.",
    },
    "Temporal.io / Inngest (Durable Execution Engine)": {
        "name": "Temporal.io Durable Execution Engine",
        "mode": "Full Reverse Engineering",
        "notes": "Focus on: Event sourcing replay architecture, deterministic workflow constraints, gRPC worker communication, timer wheels, and state persistence.",
    },
}
