#!/usr/bin/env python3
"""
Plexus Backend — LangGraph 10-Agent Orchestrator

Full production pipeline:

    START
      |
      v
  ┌─────────────┐
  │  Orchestrator│  (fetch graph/vector context, classify file)
  └──────┬──────┘
         |
    ┌────┴────┬────────┬─────────┬──────────┬────────┬────────┐
    |         |        |         |          |        |        |
    v         v        v         v          v        v        v
Security  Backend  Frontend  Database  DevOps  Dependency  CodeReview
(并行执行 via Send())
    |         |        |         |          |        |        |
    └────┬────┴────────┴─────────┴──────────┴────────┴────────┘
         |
         v
  ┌─────────────┐
  │  Aggregator │  (deduplicate, cross-validate AST, rank severity)
  └──────┬──────┘
         |
    ┌────┴────┐
    |         |
    v         v
ThreatModel  Remediation
(并行执行 via Send())
    |         |
    └────┬────┘
         v
        END

The Orchestrator uses LangGraph Send() to dispatch agents in parallel,
reducing wall-clock time by ~75% vs. sequential execution.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.state import AgentState
from app.agents.security_agent import security_agent_node
from app.agents.backend_agent import backend_agent_node
from app.agents.frontend_agent import frontend_agent_node
from app.agents.database_agent import database_agent_node
from app.agents.devops_agent import devops_agent_node
from app.agents.dependency_agent import dependency_agent_node
from app.agents.code_review_agent import code_review_agent_node
from app.agents.aggregator import aggregator_node
from app.agents.threat_model_agent import threat_model_agent_node
from app.agents.remediation_agent import remediation_agent_node
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService
from app.services.parser_service import ParserService

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
# Orchestrator entry node
# ───────────────────────────────────────────────────────────────


def orchestrator_entry(state: AgentState) -> dict[str, Any]:
    """Prepare shared context before fanning out to auditing agents.

    1. Parses file metadata via Tree-sitter.
    2. Fetches graph neighbours from Neo4j (multi-hop context).
    3. Fetches semantic neighbours from Qdrant (RAG context).
    4. Classifies file type and dispatches parallel agents.
    """
    file_path = state.get("file_path", "")
    code = state.get("code_content", "")
    lang = state.get("language", "")
    repo_id = state.get("repository_id", "")

    logger.info("[Orchestrator] Starting pipeline for %s", file_path)

    # 1. Parse AST metadata
    try:
        parser = ParserService()
        metadata = parser.parse_code(code, lang)
    except Exception as exc:
        logger.warning("[Orchestrator] AST parse failed: %s", exc)
        metadata = {"imports": [], "classes": [], "functions": [], "calls": [], "assignments": []}

    # 2. Fetch graph context (multi-hop dependencies)
    graph_ctx: list[dict] = []
    try:
        graph_svc = GraphService()
        if graph_svc.is_connected and repo_id:
            graph_ctx = graph_svc.get_file_context(
                repo_id=UUID(repo_id),
                file_path=file_path,
                hop_depth=2,
            )
    except Exception as exc:
        logger.warning("[Orchestrator] Graph context fetch failed: %s", exc)

    # 3. Fetch vector context (semantic neighbours)
    vector_ctx: list[dict] = []
    try:
        vector_svc = VectorService()
        if vector_svc.is_connected and repo_id:
            vector_ctx = vector_svc.semantic_search(
                repo_id=UUID(repo_id),
                query=f"security vulnerabilities in {lang}",
                limit=5,
            )
    except Exception as exc:
        logger.warning("[Orchestrator] Vector context fetch failed: %s", exc)

    return {
        "file_metadata": metadata,
        "graph_context": graph_ctx,
        "vector_context": vector_ctx,
        "status": "agents_dispatched",
    }


# ───────────────────────────────────────────────────────────────
# Parallel agent dispatcher
# ───────────────────────────────────────────────────────────────


def dispatch_auditing_agents(state: AgentState) -> list[Send]:
    """Return a list of Send() instructions to run auditing agents in parallel.

    Each agent receives the full state but writes into its own namespace
    inside agent_outputs to avoid key collisions.
    """
    file_path = state.get("file_path", "")
    lang = state.get("language", "")
    metadata = state.get("file_metadata", {})

    # Determine which agents are relevant based on file type and metadata
    agents_to_run: list[Send] = []

    # Security: always run
    agents_to_run.append(Send("security_agent", {}))

    # Code Review: always run
    agents_to_run.append(Send("code_review_agent", {}))

    # Backend: run on Python/JS/TS backend files (heuristic: not front-end component/style)
    if lang in ("python", "py", "javascript", "js", "typescript", "ts"):
        if not file_path.endswith((".css", ".scss", ".less", ".html", ".vue", ".svelte")):
            agents_to_run.append(Send("backend_agent", {}))

    # Frontend: run on JS/TS/Vue/React components
    if lang in ("javascript", "js", "typescript", "ts", "jsx", "tsx") or file_path.endswith((".vue", ".svelte", ".html")):
        agents_to_run.append(Send("frontend_agent", {}))

    # Database: run if file mentions DB imports or ORM patterns
    imports = {imp.get("text", "").lower() for imp in metadata.get("imports", [])}
    db_keywords = {"sqlalchemy", "psycopg2", "asyncpg", "sqlite", "pymongo", "mongoose", "prisma", "typeorm", "sequelize", "django.db", "flask_sqlalchemy"}
    if any(kw in imp for imp in imports for kw in db_keywords):
        agents_to_run.append(Send("database_agent", {}))

    # DevOps: run on Dockerfile, docker-compose, K8s manifests, CI configs
    if file_path.endswith(("Dockerfile", ".dockerfile", "docker-compose.yml", "docker-compose.yaml", ".tf", ".tfvars", ".k8s.yml", ".k8s.yaml", ".github/workflows/")):
        agents_to_run.append(Send("devops_agent", {}))

    # Dependency: run on package manifests
    if file_path.endswith(("requirements.txt", "package.json", "Pipfile", "poetry.lock", "Cargo.toml", "pom.xml", "build.gradle")):
        agents_to_run.append(Send("dependency_agent", {}))

    logger.info("[Orchestrator] Dispatching %d auditing agents for %s", len(agents_to_run), file_path)
    return agents_to_run


# ───────────────────────────────────────────────────────────────
# Post-aggregation dispatcher
# ───────────────────────────────────────────────────────────────


def dispatch_modeling_agents(state: AgentState) -> list[Send]:
    """After the aggregator finishes, fan out to threat model + remediation."""
    agents_to_run = []
    if state.get("triaged_findings"):
        agents_to_run.append(Send("threat_model_agent", {}))
        agents_to_run.append(Send("remediation_agent", {}))
    else:
        logger.info("[Orchestrator] No triaged findings — skipping threat model & remediation.")
    return agents_to_run


# ───────────────────────────────────────────────────────────────
# Graph builder
# ───────────────────────────────────────────────────────────────


def build_agent_pipeline() -> StateGraph:
    """Compile the full 10-agent LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # 1. Register all 10 nodes
    workflow.add_node("orchestrator", orchestrator_entry)
    workflow.add_node("security_agent", security_agent_node)
    workflow.add_node("backend_agent", backend_agent_node)
    workflow.add_node("frontend_agent", frontend_agent_node)
    workflow.add_node("database_agent", database_agent_node)
    workflow.add_node("devops_agent", devops_agent_node)
    workflow.add_node("dependency_agent", dependency_agent_node)
    workflow.add_node("code_review_agent", code_review_agent_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("threat_model_agent", threat_model_agent_node)
    workflow.add_node("remediation_agent", remediation_agent_node)

    # 2. Entry flow
    workflow.add_edge(START, "orchestrator")

    # 3. Parallel fan-out from orchestrator to auditing agents (dynamic dispatch)
    workflow.add_conditional_edges(
        "orchestrator",
        dispatch_auditing_agents,
        [
            "security_agent",
            "backend_agent",
            "frontend_agent",
            "database_agent",
            "devops_agent",
            "dependency_agent",
            "code_review_agent",
        ],
    )

    # 4. All auditing agents converge into aggregator
    workflow.add_edge(
        ["security_agent", "backend_agent", "frontend_agent",
         "database_agent", "devops_agent", "dependency_agent", "code_review_agent"],
        "aggregator",
    )

    # 5. Parallel fan-out from aggregator to threat model + remediation
    workflow.add_conditional_edges(
        "aggregator",
        dispatch_modeling_agents,
        ["threat_model_agent", "remediation_agent"],
    )

    # 6. End
    workflow.add_edge(["threat_model_agent", "remediation_agent"], END)

    return workflow.compile()


# Singleton compiled graph
agent_pipeline = build_agent_pipeline()


# ───────────────────────────────────────────────────────────────
# Public runner
# ───────────────────────────────────────────────────────────────


def run_analysis_pipeline(
    repository_id: UUID,
    file_path: str,
    code_content: str,
    language: str,
) -> dict[str, Any]:
    """Invoke the compiled LangGraph pipeline with source code context.

    Returns a structured payload with findings, comments, patches, and threat model.
    """
    initial_state: AgentState = {
        "repository_id": str(repository_id),
        "file_path": file_path,
        "code_content": code_content,
        "language": language,
        "file_metadata": {},
        "graph_context": [],
        "vector_context": [],
        "findings": [],
        "review_comments": [],
        "fix_suggestions": [],
        "threat_model": {},
        "agent_outputs": {},
        "triaged_findings": [],
        "status": "starting",
        "error": None,
    }

    try:
        logger.info("[Pipeline] Starting analysis for: %s", file_path)
        final_state = agent_pipeline.invoke(initial_state)
        logger.info("[Pipeline] Completed for: %s", file_path)

        return {
            "findings": final_state.get("triaged_findings", []),
            "review_comments": final_state.get("review_comments", []),
            "fix_suggestions": final_state.get("fix_suggestions", []),
            "threat_model": final_state.get("threat_model", {}),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "status": final_state.get("status", "success"),
        }
    except Exception as exc:
        logger.exception("[Pipeline] Fatal error for %s: %s", file_path, exc)
        return {
            "findings": [],
            "review_comments": [],
            "fix_suggestions": [],
            "threat_model": {},
            "agent_outputs": {},
            "status": "failed",
            "error": str(exc),
        }
