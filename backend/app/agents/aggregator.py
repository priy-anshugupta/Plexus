#!/usr/bin/env python3
"""
Plexus Backend — Aggregator & Cross-Validator Agent

Deduplicates findings from all parallel auditing agents, cross-validates
against AST metadata and static rules, and produces a ranked triaged list.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.state import AgentState

logger = logging.getLogger(__name__)


def _hash_finding(f: dict) -> str:
    """Create a deterministic hash key for deduplication."""
    return f"{f.get('rule_id', 'unknown')}:{f.get('file_path', '')}:{f.get('line_start', 0)}:{f.get('title', '')[:40]}"


def _severity_rank(sev: str) -> int:
    """Numeric rank for sorting: lower = more severe."""
    mapping = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    return mapping.get(sev.lower(), 5)


def aggregator_node(state: AgentState) -> dict[str, Any]:
    """Aggregator node: deduplicate, cross-validate, and rank findings."""
    logger.info("[Aggregator] Processing findings from all agents")

    all_findings = state.get("findings", [])
    metadata = state.get("file_metadata", {})
    code = state.get("code_content", "")
    lines = code.splitlines()

    # Deduplication using hash keys
    seen: set[str] = set()
    unique: list[dict] = []
    for f in all_findings:
        key = _hash_finding(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)
        else:
            logger.debug("[Aggregator] Deduplicated finding: %s", key)

    # Cross-validation: boost confidence if AST evidence supports the claim
    for f in unique:
        rule = f.get("rule_id", "")
        line_start = f.get("line_start", 1)
        line_end = f.get("line_end", line_start)
        confidence = f.get("confidence_score", 0.5)

        # Cross-validate hardcoded secrets against AST assignments
        if rule == "SEC-HARDCODED-SECRET" or rule == "BE-HARDCODED-SECRET":
            for assign in metadata.get("assignments", []):
                if assign.get("line") == line_start:
                    confidence = min(1.0, confidence + 0.15)
                    break

        # Cross-validate SQL injection against AST call nodes
        if rule == "SEC-SQL-INJECTION" or rule == "DB-RAW-SQL":
            for call in metadata.get("calls", []):
                if call.get("line") == line_start:
                    confidence = min(1.0, confidence + 0.1)
                    break

        # Downgrade confidence if line is just a comment or string literal
        try:
            for ln in range(line_start - 1, line_end):
                if ln < len(lines):
                    stripped = lines[ln].strip()
                    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
                        confidence = max(0.0, confidence - 0.2)
        except Exception:
            pass

        f["confidence_score"] = round(confidence, 2)

    # Rank by severity then confidence
    unique.sort(key=lambda f: (_severity_rank(f.get("severity", "info")), -f.get("confidence_score", 0)))

    # Filter out low-confidence noise (< 0.3) for triaged list
    triaged = [f for f in unique if f.get("confidence_score", 0) >= 0.3]

    logger.info("[Aggregator] %d raw findings -> %d unique -> %d triaged", len(all_findings), len(unique), len(triaged))

    return {
        "triaged_findings": triaged,
        "findings": unique,  # overwrite with deduplicated list
        "status": "aggregated",
    }
