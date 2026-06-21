#!/usr/bin/env python3
"""
Plexus Backend — Frontend Agent

Audits frontend code (React, Vue, vanilla JS/TS) for DOM XSS, memory leaks,
stale closures, insecure innerHTML usage, and package vulnerabilities.
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


class FrontendFindingSchema(BaseModel):
    title: str = Field(..., description="Frontend issue summary, e.g. 'DOM XSS via innerHTML'.")
    description: str = Field(..., description="Detailed explanation of the frontend flaw.")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    severity: str = Field(..., description="critical | high | medium | low | info")
    rule_id: str = Field(..., description="FE-DOM-XSS, FE-INNER-HTML, FE-MEMORY-LEAK, etc.")
    suggestion: str = Field(..., description="Actionable fix.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class FrontendReportSchema(BaseModel):
    findings: list[FrontendFindingSchema] = Field(default_factory=list)


def frontend_agent_node(state: AgentState) -> dict[str, Any]:
    """Frontend audit node."""
    logger.info("[FrontendAgent] Analysing %s", state.get("file_path"))
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
            structured = llm.with_structured_output(FrontendReportSchema)
            system = (
                "You are a frontend security expert. Audit the code for: "
                "DOM-based XSS (innerHTML, dangerouslySetInnerHTML), missing useEffect cleanup (memory leaks), "
                "stale closures, insecure event listeners, unsafe eval in React/Vue, "
                "missing CSRF tokens on fetch requests, and package vulnerabilities. "
                "Be precise with line numbers and React/Vue specifics."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=f"Language: {lang}\nFile: {file_path}\n\n{code}")])
            for f in report.findings:
                findings.append({
                    "title": f.title, "description": f.description, "line_start": f.line_start,
                    "line_end": f.line_end, "severity": f.severity.lower(), "category": "frontend",
                    "status": "open", "suggestion": f.suggestion, "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score, "is_ai_generated": True,
                })
            logger.info("[FrontendAgent] AI found %d issues", len(findings))
        except Exception as exc:
            logger.warning("[FrontendAgent] AI failed: %s. Falling back to static.", exc)

    # Static fallback
    if not findings:
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            ln = idx + 1
            low = line.lower()
            if "dangerouslysetinnerhtml" in low or "innerhtml" in low:
                findings.append({
                    "title": "Unsafe innerHTML Usage", "description": "Setting innerHTML with unsanitized data can lead to DOM XSS.",
                    "line_start": ln, "line_end": ln, "severity": "high", "category": "frontend",
                    "status": "open", "suggestion": "Use textContent or sanitize with DOMPurify before setting innerHTML.", "rule_id": "FE-DOM-XSS",
                    "confidence_score": 0.9, "is_ai_generated": False,
                })
            if "eval(" in low or "function(" in low and "constructor" in low:
                findings.append({
                    "title": "Unsafe Dynamic Code Execution", "description": "eval or Function constructor usage is dangerous in browser code.",
                    "line_start": ln, "line_end": ln, "severity": "critical", "category": "frontend",
                    "status": "open", "suggestion": "Replace with safe JSON.parse or explicit parsing logic.", "rule_id": "FE-UNSAFE-EVAL",
                    "confidence_score": 0.95, "is_ai_generated": False,
                })
            if "useeffect" in low and "return" not in low and "cleanup" not in low:
                # Naive heuristic: useEffect without cleanup and with subscriptions/timers
                if "setinterval" in low or "addeventlistener" in low or "websocket" in low:
                    findings.append({
                        "title": "Potential Memory Leak in useEffect", "description": "useEffect sets up a subscription or listener but may not clean it up.",
                        "line_start": ln, "line_end": min(ln + 5, len(lines)), "severity": "medium", "category": "frontend",
                        "status": "open", "suggestion": "Return a cleanup function from useEffect to remove listeners/subscriptions.", "rule_id": "FE-MEMORY-LEAK",
                        "confidence_score": 0.7, "is_ai_generated": False,
                    })

    return {"findings": findings, "agent_outputs": {"frontend_agent": findings}}
