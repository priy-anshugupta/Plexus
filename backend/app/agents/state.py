#!/usr/bin/env python3
"""
Plexus Backend — Unified Agent State

Rich shared state tracking for the full 10-agent LangGraph pipeline.
Includes per-agent outputs, graph context, metadata, and final payload.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict, Optional


class AgentState(TypedDict):
    """Shared state passed through the LangGraph pipeline.

    Fields
    ------
    repository_id : str
        Target repository UUID.
    file_path : str
        Relative file path under analysis.
    code_content : str
        Raw source code text.
    language : str
        Programming language (python, javascript, etc.).
    file_metadata : dict
        Parsed AST summary (imports, classes, functions, calls, assignments).
    graph_context : list[dict]
        Relevant subgraph nodes/edges fetched from Neo4j for multi-hop reasoning.
    vector_context : list[dict]
        Semantic neighbours retrieved from Qdrant for RAG context.
    findings : list[dict]
        Aggregated security vulnerabilities (added via operator.add).
    review_comments : list[dict]
        Aggregated code-quality comments (added via operator.add).
    fix_suggestions : list[dict]
        Aggregated auto-fix patches (added via operator.add).
    threat_model : dict
        STRIDE threat model output (added by Threat Model Agent).
    agent_outputs : dict[str, list[dict]]
        Raw per-agent outputs keyed by agent name.
    triaged_findings : list[dict]
        Deduplicated, cross-validated, ranked findings (added by Aggregator).
    status : str
        Pipeline lifecycle status.
    error : str | None
        Global error message if the pipeline fails.
    """

    repository_id: str
    file_path: str
    code_content: str
    language: str
    file_metadata: Annotated[dict, operator.or_]
    graph_context: Annotated[list[dict], operator.add]
    vector_context: Annotated[list[dict], operator.add]
    findings: Annotated[list[dict], operator.add]
    review_comments: Annotated[list[dict], operator.add]
    fix_suggestions: Annotated[list[dict], operator.add]
    threat_model: Annotated[dict, operator.or_]
    agent_outputs: Annotated[dict[str, list[dict]], operator.or_]
    triaged_findings: Annotated[list[dict], operator.add]
    status: str
    error: Optional[str]
