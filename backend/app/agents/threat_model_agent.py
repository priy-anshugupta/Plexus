#!/usr/bin/env python3
"""
Plexus Backend — Threat Model Agent

Analyses the compiled code property graph and findings to generate a STRIDE
threat model automatically, mapping Spoofing, Tampering, Repudiation, Information
Disclosure, Denial of Service, and Elevation of Privilege risks.
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


class STRIDEFindingSchema(BaseModel):
    category: str = Field(..., description="STRIDE category: Spoofing, Tampering, Repudiation, InfoDisclosure, DoS, Elevation.")
    description: str = Field(..., description="Threat description mapped to the architecture.")
    affected_components: list[str] = Field(default_factory=list, description="Code components affected.")
    mitigations: list[str] = Field(default_factory=list, description="Recommended mitigations.")
    severity: str = Field(..., description="critical | high | medium | low")


class STRIDEReportSchema(BaseModel):
    threats: list[STRIDEFindingSchema] = Field(default_factory=list)
    summary: str = Field(..., description="Executive summary of the threat model.")
    risk_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100.")


def threat_model_agent_node(state: AgentState) -> dict[str, Any]:
    """Threat model generation node."""
    logger.info("[ThreatModelAgent] Generating STRIDE model for %s", state.get("file_path"))
    findings = state.get("triaged_findings", [])
    graph_ctx = state.get("graph_context", [])
    code = state.get("code_content", "")
    lang = state.get("language", "")
    file_path = state.get("file_path", "")

    if not findings:
        return {"threat_model": {"threats": [], "summary": "No findings to model.", "risk_score": 0}}

    cloud_allowed = (
        settings.openai_api_key
        and len(code) <= settings.agent_max_source_chars
        and not PrivacyService().contains_sensitive_data(code)
    )

    if cloud_allowed:
        try:
            llm = ChatOpenAI(model=settings.openai_model, temperature=0.0, openai_api_key=settings.openai_api_key)
            structured = llm.with_structured_output(STRIDEReportSchema)
            system = (
                "You are a threat modeling architect using the STRIDE methodology. "
                "Given the security findings and code context, produce a system-level threat model. "
                "Map each finding to STRIDE categories, identify affected components, "
                "and suggest architectural mitigations. Return a concise executive summary and risk score (0-100)."
            )
            prompt = (
                f"File: {file_path}\nLanguage: {lang}\n\n"
                f"Triaged Findings:\n{findings}\n\n"
                f"Graph Context (dependencies):\n{graph_ctx}\n\n"
                f"Generate a STRIDE threat model."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=prompt)])
            model = {
                "threats": [
                    {
                        "category": t.category,
                        "description": t.description,
                        "affected_components": t.affected_components,
                        "mitigations": t.mitigations,
                        "severity": t.severity.lower(),
                    }
                    for t in report.threats
                ],
                "summary": report.summary,
                "risk_score": report.risk_score,
            }
            logger.info("[ThreatModelAgent] Generated model with %d threats, risk=%d", len(report.threats), report.risk_score)
            return {"threat_model": model}
        except Exception as exc:
            logger.warning("[ThreatModelAgent] AI failed: %s", exc)

    # Static fallback: map known rule_ids to STRIDE categories
    threats = []
    for f in findings:
        rule = f.get("rule_id", "")
        title = f.get("title", "")
        if "SQL" in title or "INJECTION" in title:
            threats.append({"category": "Tampering", "description": f"{title} allows tampering with database queries.", "affected_components": [file_path], "mitigations": ["Use parameterized queries"], "severity": "critical"})
        if "HARDCODED" in title or "SECRET" in title:
            threats.append({"category": "Information Disclosure", "description": f"{title} exposes credentials.", "affected_components": [file_path], "mitigations": ["Use secret manager"], "severity": "high"})
        if "XSS" in title or "DOM" in title:
            threats.append({"category": "Tampering", "description": f"{title} allows script injection.", "affected_components": [file_path], "mitigations": ["Sanitize output"], "severity": "high"})
        if "AUTH" in title or "BYPASS" in title:
            threats.append({"category": "Elevation", "description": f"{title} may allow unauthorized access.", "affected_components": [file_path], "mitigations": ["Enforce RBAC"], "severity": "critical"})
        if "RACE" in title or "DoS" in title:
            threats.append({"category": "Denial of Service", "description": f"{title} may lead to resource exhaustion.", "affected_components": [file_path], "mitigations": ["Add rate limiting"], "severity": "medium"})

    risk_score = min(100, len(threats) * 15)
    return {"threat_model": {"threats": threats, "summary": f"Static STRIDE mapping produced {len(threats)} threats.", "risk_score": risk_score}}
