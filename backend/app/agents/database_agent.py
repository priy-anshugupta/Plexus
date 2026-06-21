#!/usr/bin/env python3
"""
Plexus Backend — Database Agent

Audits database interactions for N+1 query loops, missing indexes,
unsafe raw SQL, unoptimized migrations, and connection pool exhaustion.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.state import AgentState
from app.services.privacy_service import PrivacyService

logger = logging.getLogger(__name__)


class DatabaseFindingSchema(BaseModel):
    title: str = Field(..., description="DB issue summary, e.g. 'N+1 Query Loop'.")
    description: str = Field(..., description="Detailed explanation of the database flaw.")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    severity: str = Field(..., description="critical | high | medium | low | info")
    rule_id: str = Field(..., description="DB-N-PLUS-ONE, DB-RAW-SQL, DB-MISSING-INDEX, etc.")
    suggestion: str = Field(..., description="Actionable fix.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class DatabaseReportSchema(BaseModel):
    findings: list[DatabaseFindingSchema] = Field(default_factory=list)


def database_agent_node(state: AgentState) -> dict[str, Any]:
    """Database audit node."""
    logger.info("[DatabaseAgent] Analysing %s", state.get("file_path"))
    code = state.get("code_content", "")
    lang = state.get("language", "")
    file_path = state.get("file_path", "")

    findings = []
    cloud_allowed = (
        settings.openai_api_key
        and len(code) <= settings.agent_max_source_chars
        and not PrivacyService().contains_sensitive_data(code)
    )

    if cloud_allowed:
        try:
            llm = ChatOpenAI(model=settings.openai_model, temperature=0.0, openai_api_key=settings.openai_api_key)
            structured = llm.with_structured_output(DatabaseReportSchema)
            system = (
                "You are a database performance & security specialist. "
                "Audit the code for: N+1 query loops (iterating over objects and calling DB per item), "
                "missing index hints on query filters, raw SQL injection vectors, "
                "unbatched bulk inserts, missing transaction wrappers, "
                "and connection pool exhaustion patterns. "
                "Be precise with line numbers and ORM-specific recommendations."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=f"Language: {lang}\nFile: {file_path}\n\n{code}")])
            for f in report.findings:
                findings.append({
                    "title": f.title, "description": f.description, "line_start": f.line_start,
                    "line_end": f.line_end, "severity": f.severity.lower(), "category": "database",
                    "status": "open", "suggestion": f.suggestion, "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score, "is_ai_generated": True,
                })
            logger.info("[DatabaseAgent] AI found %d issues", len(findings))
        except Exception as exc:
            logger.warning("[DatabaseAgent] AI failed: %s. Falling back to static.", exc)

    # Static fallback
    if not findings:
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            ln = idx + 1
            low = line.lower()
            # N+1 heuristic: for loop with DB call inside
            if low.strip().startswith("for "):
                # Look ahead 5 lines for a DB query pattern
                for j in range(idx + 1, min(idx + 6, len(lines))):
                    if any(k in lines[j].lower() for k in (".query(", ".filter(", ".get(", ".find(", ".all(", ".execute(")):
                        findings.append({
                            "title": "Potential N+1 Query Loop", "description": "A loop contains a database query which will execute N times.",
                            "line_start": ln, "line_end": j + 1, "severity": "medium", "category": "database",
                            "status": "open", "suggestion": "Use eager loading (join, selectinload) or batch queries before the loop.", "rule_id": "DB-N-PLUS-ONE",
                            "confidence_score": 0.65, "is_ai_generated": False,
                        })
                        break
            # Raw SQL with string interpolation
            if any(k in low for k in ("raw(", "text(", "execute(")) and ("f\"" in line or "f'" in line or "%" in line or "+" in line):
                findings.append({
                    "title": "Unsafe Raw SQL Execution", "description": "Raw SQL query appears to use string interpolation or concatenation.",
                    "line_start": ln, "line_end": ln, "severity": "high", "category": "database",
                    "status": "open", "suggestion": "Use parameterized queries or ORM query builders instead of raw string SQL.", "rule_id": "DB-RAW-SQL",
                    "confidence_score": 0.8, "is_ai_generated": False,
                })

    return {"findings": findings, "agent_outputs": {"database_agent": findings}}
