"""
Plexus Backend — Security Analyzer Agent

AI agent responsible for triaging and auditing source code for security
vulnerabilities (SQLi, XSS, CSRF, RCE, hardcoded secrets) using ChatOpenAI.
Includes a static rules engine fallback for offline execution.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.state import AgentState
from app.services.scanner_service import ScannerService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Output Schema (Pydantic)
# ---------------------------------------------------------------------------

class SecurityFindingSchema(BaseModel):
    """Structured representation of a single security vulnerability."""

    title: str = Field(..., description="Short summary of the security issue, e.g. 'SQL Injection'.")
    description: str = Field(..., description="Detailed description explaining why the code is vulnerable.")
    line_start: int = Field(..., ge=1, description="Starting line number of the vulnerability.")
    line_end: int = Field(..., ge=1, description="Ending line number (inclusive).")
    severity: str = Field(
        ...,
        description="Severity level — must be one of: 'critical', 'high', 'medium', 'low', 'info'.",
    )
    rule_id: str = Field(
        ...,
        description="Standardised rule identifier, e.g. 'SEC-SQL-INJECTION', 'SEC-HARDCODED-SECRET'.",
    )
    suggestion: str = Field(..., description="Actionable remediation guidance or recommended fix code.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the finding (0.0-1.0).")


class SecurityReportSchema(BaseModel):
    """Unified collection of security findings returned by the model."""

    findings: list[SecurityFindingSchema] = Field(
        default_factory=list,
        description="Collection of security findings discovered inside the code.",
    )


# ---------------------------------------------------------------------------
# Agent Node Function
# ---------------------------------------------------------------------------

def security_agent_node(state: AgentState) -> dict[str, any]:
    """LangGraph node representing the Security Agent.

    Inspects code using GPT models to find issues, falling back to static
    regex/AST rules if offline or missing API keys.
    """
    logger.info("Executing Security Agent node for file: %s", state.get("file_path"))
    
    code = state.get("code_content", "")
    lang = state.get("language", "")
    file_path = state.get("file_path", "")
    repo_id_str = state.get("repository_id", "")

    # 1. Try AI Analysis if key is available
    if settings.openai_api_key:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                openai_api_key=settings.openai_api_key,
            )
            structured_llm = llm.with_structured_output(SecurityReportSchema)

            system_instruction = (
                "You are an expert static application security analysis (SAST) agent. "
                "Audit the provided source code for vulnerabilities: SQL Injection, "
                "Cross-Site Scripting (XSS), Path Traversal, Remote Code Execution (RCE), "
                "Hardcoded Credentials, or broken authorization. "
                "Be extremely precise. Give accurate line numbers. "
                "Provide actionable suggestion comments for remediation."
            )
            user_prompt = f"Language: {lang}\nFile: {file_path}\n\nCode Content:\n{code}"

            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content=user_prompt),
            ]

            report = structured_llm.invoke(messages)
            
            # Map Pydantic schema output back to ORM/JSON dict formats
            findings = []
            for f in report.findings:
                findings.append({
                    "title": f.title,
                    "description": f.description,
                    "line_start": f.line_start,
                    "line_end": f.line_end,
                    "severity": f.severity.lower(),
                    "category": "security",
                    "status": "open",
                    "suggestion": f.suggestion,
                    "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score,
                    "is_ai_generated": True,
                })
            
            logger.info("AI Security Scan completed with %d findings.", len(findings))
            return {"findings": findings}

        except Exception as exc:
            logger.warning("AI Security Scan failed: %s. Falling back to static rules.", exc)

    # 2. Fallback: Run static scanner rules
    try:
        scanner = ScannerService()
        static_findings = scanner._analyze_file(
            relative_path=file_path,
            code_content=code,
            language=lang,
            scan_id=uuid4(),
            repo_id=uuid4(),
        )
        
        findings = []
        for f in static_findings:
            findings.append({
                "title": f.title,
                "description": f.description,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "severity": f.severity.value,
                "category": "security",
                "status": "open",
                "suggestion": f.suggestion,
                "rule_id": f.rule_id,
                "confidence_score": f.confidence_score,
                "is_ai_generated": False,
            })
            
        logger.info("Static Fallback Scan completed with %d findings.", len(findings))
        return {"findings": findings}
    except Exception as exc:
        logger.error("Static scanner fallback failed: %s", exc)
        return {"findings": []}
