#!/usr/bin/env python3
"""
Plexus Backend — Backend Agent

Audits server-side code for API validation gaps, unhandled exceptions,
race conditions, business logic flaws, and insecure deserialization.
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


class BackendFindingSchema(BaseModel):
    title: str = Field(..., description="Backend issue summary, e.g. 'Unvalidated Path Parameter'.")
    description: str = Field(..., description="Detailed explanation of the backend flaw.")
    line_start: int = Field(..., ge=1, description="Starting line number.")
    line_end: int = Field(..., ge=1, description="Ending line number (inclusive).")
    severity: str = Field(..., description="critical | high | medium | low | info")
    rule_id: str = Field(..., description="Standardised rule, e.g. 'BE-UNVALIDATED-INPUT', 'BE-RACE-CONDITION'.")
    suggestion: str = Field(..., description="Actionable fix or refactoring guidance.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class BackendReportSchema(BaseModel):
    findings: list[BackendFindingSchema] = Field(default_factory=list)


def backend_agent_node(state: AgentState) -> dict[str, Any]:
    """Backend audit node."""
    logger.info("[BackendAgent] Analysing %s", state.get("file_path"))
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
            structured = llm.with_structured_output(BackendReportSchema)
            system = (
                "You are a backend security & reliability specialist. "
                "Audit the code for: unvalidated input/path parameters, unhandled exceptions, "
                "race conditions (async/await, threading), broken auth logic, insecure deserialization, "
                "missing rate limiting, and business logic flaws. "
                "Be precise with line numbers and provide actionable remediation."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=f"Language: {lang}\nFile: {file_path}\n\n{code}")])
            for f in report.findings:
                findings.append({
                    "title": f.title, "description": f.description, "line_start": f.line_start,
                    "line_end": f.line_end, "severity": f.severity.lower(), "category": "backend",
                    "status": "open", "suggestion": f.suggestion, "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score, "is_ai_generated": True,
                })
            logger.info("[BackendAgent] AI found %d issues", len(findings))
        except Exception as exc:
            logger.warning("[BackendAgent] AI failed: %s. Falling back to static.", exc)

    # Static fallback: look for common backend anti-patterns
    if not findings:
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            ln = idx + 1
            stripped = line.strip().lower()
            if stripped.startswith("eval(") or stripped.startswith("exec("):
                findings.append({
                    "title": "Unsafe Dynamic Execution", "description": "Direct eval/exec usage is dangerous and allows code injection.",
                    "line_start": ln, "line_end": ln, "severity": "critical", "category": "backend",
                    "status": "open", "suggestion": "Replace with explicit parsers or safe APIs.", "rule_id": "BE-UNSAFE-EXEC",
                    "confidence_score": 0.95, "is_ai_generated": False,
                })
            if "request.args.get" in stripped and "(" in stripped:
                # Very naive heuristic for unvalidated Flask input
                if idx + 1 < len(lines) and "validate" not in lines[idx + 1].lower():
                    findings.append({
                        "title": "Potentially Unvalidated Request Input", "description": "Request parameter retrieved without visible validation.",
                        "line_start": ln, "line_end": ln, "severity": "medium", "category": "backend",
                        "status": "open", "suggestion": "Add explicit input validation or schema validation.", "rule_id": "BE-UNVALIDATED-INPUT",
                        "confidence_score": 0.6, "is_ai_generated": False,
                    })

    return {"findings": findings, "agent_outputs": {"backend_agent": findings}}
