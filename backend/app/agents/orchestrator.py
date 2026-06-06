"""
Plexus Backend — LangGraph Agent Orchestrator

Defines and compiles the LangGraph StateGraph, wiring the security agent,
code review agent, and auto-fix suggestions agent into a unified pipeline.
"""

from __future__ import annotations

import logging
from uuid import UUID

from langgraph.graph import END, StateGraph

from app.agents.autofix_agent import autofix_agent_node
from app.agents.code_review_agent import code_review_agent_node
from app.agents.security_agent import security_agent_node
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph Workflow Construction
# ---------------------------------------------------------------------------

def create_agent_workflow() -> StateGraph:
    """Builds and compiles the multi-agent execution state graph."""
    workflow = StateGraph(AgentState)

    # 1. Register agent nodes
    workflow.add_node("security_analyser", security_agent_node)
    workflow.add_node("code_reviewer", code_review_agent_node)
    workflow.add_node("autofix_generator", autofix_agent_node)

    # 2. Wire nodes (Linear pipeline)
    workflow.set_entry_point("security_analyser")
    workflow.add_edge("security_analyser", "code_reviewer")
    workflow.add_edge("code_reviewer", "autofix_generator")
    workflow.add_edge("autofix_generator", END)

    # 3. Compile the graph
    return workflow.compile()


# Singleton compiled graph app
agent_pipeline_app = create_agent_workflow()


# ---------------------------------------------------------------------------
# Runner API
# ---------------------------------------------------------------------------

def run_analysis_pipeline(
    repository_id: UUID,
    file_path: str,
    code_content: str,
    language: str,
) -> dict:
    """Invokes the compiled LangGraph pipeline with the given source code context.

    Runs all analysis nodes and returns the compiled state.

    Args:
        repository_id: Repository UUID.
        file_path: Relative file path.
        code_content: Code contents to inspect.
        language: Programming language.

    Returns:
        A dictionary containing final findings, review comments, and suggestions:
        {
            "findings": [...],
            "review_comments": [...],
            "fix_suggestions": [...]
        }
    """
    initial_state: AgentState = {
        "repository_id": str(repository_id),
        "file_path": file_path,
        "code_content": code_content,
        "language": language,
        "findings": [],
        "review_comments": [],
        "fix_suggestions": [],
        "status": "starting",
    }

    try:
        logger.info("Starting LangGraph agent analysis pipeline for: %s", file_path)
        final_state = agent_pipeline_app.invoke(initial_state)
        logger.info("LangGraph agent pipeline finished successfully for: %s", file_path)
        
        return {
            "findings": final_state.get("findings", []),
            "review_comments": final_state.get("review_comments", []),
            "fix_suggestions": final_state.get("fix_suggestions", []),
            "status": "success",
        }
    except Exception as exc:
        logger.exception("Error executing LangGraph agent pipeline: %s", exc)
        return {
            "findings": [],
            "review_comments": [],
            "fix_suggestions": [],
            "status": "failed",
        }
