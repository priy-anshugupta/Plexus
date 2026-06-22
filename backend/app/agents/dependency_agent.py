#!/usr/bin/env python3
"""
Plexus Backend — Dependency Agent

Integrates with OSV.dev database to flag CVEs, outdated packages, and license
compliance issues in package manifests (requirements.txt, package.json, etc.).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.state import AgentState
from app.services.privacy_service import PrivacyService

logger = logging.getLogger(__name__)

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"


class DependencyFindingSchema(BaseModel):
    title: str = Field(..., description="Dependency issue, e.g. 'CVE-2024-1234 in lodash@4.17.15'.")
    description: str = Field(..., description="Detailed CVE description or license issue.")
    line_start: int = Field(..., ge=1)
    line_end: int = Field(..., ge=1)
    severity: str = Field(..., description="critical | high | medium | low | info")
    rule_id: str = Field(..., description="DEP-CVE, DEP-OUTDATED, DEP-LICENSE, etc.")
    suggestion: str = Field(..., description="Upgrade command or replacement package.")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    cve_id: str | None = Field(default=None, description="Associated CVE identifier if known.")


class DependencyReportSchema(BaseModel):
    findings: list[DependencyFindingSchema] = Field(default_factory=list)


def _parse_requirements(content: str) -> list[dict]:
    """Parse requirements.txt into package name + version dicts."""
    packages = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        # Simple regex: package==version, package>=version, etc.
        m = re.match(r"^([a-zA-Z0-9_-]+)(?:[<>=!~]+)([\d.]+)", stripped)
        if m:
            packages.append({"name": m.group(1), "version": m.group(2)})
    return packages


def _parse_package_json(content: str) -> list[dict]:
    """Parse package.json dependencies into package name + version dicts."""
    try:
        data = json.loads(content)
        deps = {}
        deps.update(data.get("dependencies", {}))
        deps.update(data.get("devDependencies", {}))
        return [{"name": k, "version": v.lstrip("^~>=<")} for k, v in deps.items()]
    except Exception:
        return []


def _query_osv(packages: list[dict]) -> list[dict]:
    """Query OSV.dev batch API for CVEs."""
    if not packages:
        return []
    queries = [{"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]} for p in packages]
    try:
        resp = httpx.post(OSV_BATCH_URL, json={"queries": queries}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for idx, result in enumerate(data.get("results", [])):
            vulns = result.get("vulns", [])
            if vulns:
                pkg = packages[idx]
                for v in vulns:
                    severity = "medium"
                    if v.get("database_specific", {}).get("severity") == "CRITICAL":
                        severity = "critical"
                    elif v.get("database_specific", {}).get("severity") == "HIGH":
                        severity = "high"
                    results.append({
                        "title": f"{v.get('id', 'CVE')} in {pkg['name']}@{pkg['version']}",
                        "description": v.get("summary", "No summary available."),
                        "severity": severity,
                        "rule_id": "DEP-CVE",
                        "cve_id": v.get("id"),
                        "suggestion": f"Upgrade {pkg['name']} to a patched version.",
                        "confidence_score": 0.9,
                    })
        return results
    except Exception as exc:
        logger.warning("OSV query failed: %s", exc)
        return []


def dependency_agent_node(state: AgentState) -> dict[str, Any]:
    """Dependency audit node."""
    logger.info("[DependencyAgent] Analysing %s", state.get("file_path"))
    code = state.get("code_content", "")
    file_path = state.get("file_path", "")

    findings = []
    packages: list[dict] = []

    if file_path.endswith("requirements.txt"):
        packages = _parse_requirements(code)
    elif file_path.endswith("package.json"):
        packages = _parse_package_json(code)

    # OSV query for actual CVEs
    if packages:
        osv_results = _query_osv(packages)
        for r in osv_results:
            findings.append({
                **r, "line_start": 1, "line_end": 1, "category": "dependency", "status": "open", "is_ai_generated": False,
            })

    # AI layer for deeper analysis (license compliance, outdated major versions, etc.)
    cloud_allowed = (
        settings.openai_api_key
        and len(code) <= settings.agent_max_source_chars
        and not PrivacyService().contains_sensitive_data(code)
    )
    if cloud_allowed:
        try:
            llm = ChatOpenAI(model=settings.openai_model, temperature=0.0, openai_api_key=settings.openai_api_key)
            structured = llm.with_structured_output(DependencyReportSchema)
            system = (
                "You are a dependency security & compliance analyst. "
                "Audit the manifest for: known CVEs (already flagged by OSV if any), outdated major versions, "
                "abandoned packages, restrictive license conflicts (GPL vs proprietary), "
                "and packages with high supply-chain risk (new/unmaintained authors). "
                "Be precise with line numbers and suggest specific upgrade versions."
            )
            report = structured.invoke([SystemMessage(content=system), HumanMessage(content=f"File: {file_path}\n\n{code}")])
            for f in report.findings:
                findings.append({
                    "title": f.title, "description": f.description, "line_start": f.line_start,
                    "line_end": f.line_end, "severity": f.severity.lower(), "category": "dependency",
                    "status": "open", "suggestion": f.suggestion, "rule_id": f.rule_id,
                    "confidence_score": f.confidence_score, "is_ai_generated": True, "cve_id": f.cve_id,
                })
            logger.info("[DependencyAgent] AI found %d issues", len(report.findings))
        except Exception as exc:
            logger.warning("[DependencyAgent] AI failed: %s", exc)

    return {"findings": findings, "agent_outputs": {"dependency_agent": findings}}
