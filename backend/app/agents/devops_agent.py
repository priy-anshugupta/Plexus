#!/usr/bin/env python3
"""
Plexus Backend — DevOps Agent

Scans Dockerfiles, docker-compose files, Kubernetes manifests, and CI/CD
configurations for root containers, exposed secrets, and insecure capabilities.
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


class DevOpsFindingSchema(BaseModel):
    title: str = Field(..., description="DevOps issue summary, e.g. 'Container Running as Root'.")
    description: str = Field(..., description="Detailed explanation of the infrastructure flaw.")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    severity: str = Field(..., description="critical | high | medium | low | info")
    rule_id: str = Field(..., description="DO-ROOT-USER, DO-EXPOSED-SECRET, DO-INSECURE-CAP, etc.")
    suggestion: str = Field(..., description="Actionable fix.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class DevOpsReportSchema(BaseModel):
    findings: list[DevOpsFindingSchema] = Field(default_factory=list)


def devops_agent_node(state: AgentState) -> dict[str, Any]:
    """DevOps audit node."""
    logger.info("[DevOpsAgent] Analysing %s", state.get("file_path"))
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
            structured = llm.with_structured_output(DevOpsReportSchema)
            system = (
                "You are a DevOps & infrastructure security specialist. "
                "Audit the configuration for: containers running as root, missing resource limits, "
                "exposed secrets in environment variables or build args, insecure capabilities (CAP_SYS_ADMIN), "
                "missing health checks, overly broad network policies, and privileged mode. "
                "Be precise with line numbers and provide Kubernetes/Dockerfile-specific fixes."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=f"Language: {lang}\nFile: {file_path}\n\n{code}")])
            for f in report.findings:
                findings.append({
                    "title": f.title, "description": f.description, "line_start": f.line_start,
                    "line_end": f.line_end, "severity": f.severity.lower(), "category": "devops",
                    "status": "open", "suggestion": f.suggestion, "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score, "is_ai_generated": True,
                })
            logger.info("[DevOpsAgent] AI found %d issues", len(findings))
        except Exception as exc:
            logger.warning("[DevOpsAgent] AI failed: %s. Falling back to static.", exc)

    # Static fallback
    if not findings:
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            ln = idx + 1
            low = line.lower().strip()
            if "user root" in low or ("user" in low and "0" in low):
                findings.append({
                    "title": "Container Running as Root", "description": "Dockerfile sets USER root or UID 0, increasing blast radius if compromised.",
                    "line_start": ln, "line_end": ln, "severity": "high", "category": "devops",
                    "status": "open", "suggestion": "Create a non-root user with USER <uid> and run the application under that user.", "rule_id": "DO-ROOT-USER",
                    "confidence_score": 0.95, "is_ai_generated": False,
                })
            if "privileged: true" in low or "--privileged" in low:
                findings.append({
                    "title": "Privileged Container Mode", "description": "Container runs in privileged mode, granting full host access.",
                    "line_start": ln, "line_end": ln, "severity": "critical", "category": "devops",
                    "status": "open", "suggestion": "Remove privileged: true and use only required capabilities (drop ALL, add specific).", "rule_id": "DO-PRIVILEGED",
                    "confidence_score": 0.95, "is_ai_generated": False,
                })
            if "add_capabilities" in low or "capabilities:" in low:
                if "sys_admin" in low or "net_admin" in low or "sys_ptrace" in low:
                    findings.append({
                        "title": "Dangerous Capability Added", "description": "Container adds a high-risk Linux capability.",
                        "line_start": ln, "line_end": ln, "severity": "high", "category": "devops",
                        "status": "open", "suggestion": "Drop ALL capabilities and add only the minimum required set.", "rule_id": "DO-INSECURE-CAP",
                        "confidence_score": 0.9, "is_ai_generated": False,
                    })

    return {"findings": findings, "agent_outputs": {"devops_agent": findings}}
