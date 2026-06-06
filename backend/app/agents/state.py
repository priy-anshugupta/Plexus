"""
Plexus Backend — LangGraph Agent State

Defines the shared state dictionary tracking repository contexts, source code,
findings, review suggestions, and auto-fix suggestions throughout the pipeline.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    """Unified state tracking payload passed between LangGraph agent nodes.

    Includes the target context, intermediate review comments, detected
    vulnerabilities, and the generated fix patches.
    """

    repository_id: str
    file_path: str
    code_content: str
    language: str
    findings: list[dict[str, Any]]
    review_comments: list[dict[str, Any]]
    fix_suggestions: list[dict[str, Any]]
    status: str
