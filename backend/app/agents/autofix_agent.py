"""
Plexus Backend — Auto-Fix Suggestion Agent

AI agent responsible for analyzing security findings and generating precise,
drop-in code refactoring suggestions to remediate vulnerabilities.
Includes a rule-based template builder fallback for offline execution.
"""

from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Output Schema (Pydantic)
# ---------------------------------------------------------------------------

class FixSuggestionSchema(BaseModel):
    """Structured representation of a single auto-fix code block suggestion."""

    finding_title: str = Field(..., description="Title of the vulnerability being fixed.")
    line_start: int = Field(..., ge=1, description="Start line of the original code block to replace.")
    line_end: int = Field(..., ge=1, description="End line of the original code block (inclusive).")
    original_code: str = Field(..., description="The exact original vulnerable code lines.")
    corrected_code: str = Field(..., description="The recommended safe replacement code block.")
    explanation: str = Field(..., description="Description of why this fix is secure and how it works.")


class AutoFixReportSchema(BaseModel):
    """Unified collection of fix suggestions returned by the model."""

    suggestions: list[FixSuggestionSchema] = Field(
        default_factory=list,
        description="Collection of generated refactoring patches.",
    )


# ---------------------------------------------------------------------------
# Agent Node Function
# ---------------------------------------------------------------------------

def autofix_agent_node(state: AgentState) -> dict[str, any]:
    """LangGraph node representing the Auto-Fix Agent.

    Generates code refactoring suggestions for any critical/high findings,
    falling back to template-based fixes if offline or missing API keys.
    """
    logger.info("Executing Auto-Fix Agent node for file: %s", state.get("file_path"))
    
    findings = state.get("findings", [])
    code = state.get("code_content", "")
    lang = state.get("language", "")
    file_path = state.get("file_path", "")

    # Filter for severe findings that merit an automatic fix suggestion
    severe_findings = [
        f for f in findings 
        if f.get("severity", "").lower() in ("critical", "high")
    ]

    if not severe_findings:
        logger.info("No critical or high severity findings to fix.")
        return {"fix_suggestions": []}

    # 1. Try AI Generation if key is available
    if settings.openai_api_key:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                openai_api_key=settings.openai_api_key,
            )
            structured_llm = llm.with_structured_output(AutoFixReportSchema)

            system_instruction = (
                "You are an elite secure coding refactoring bot. "
                "For each provided security finding, inspect the source code "
                "and generate a precise, drop-in replacement code block. "
                "Ensure the replacement is secure (e.g. parameterised query, "
                "environment variable lookups, sanitised inputs). "
                "Keep the changes minimal and preserve the surrounding context."
            )
            
            # Format findings summaries for LLM prompt context
            findings_context = "\n\n".join([
                f"Finding: {f['title']}\n"
                f"Rule: {f['rule_id']}\n"
                f"Lines: {f['line_start']}-{f['line_end']}\n"
                f"Description: {f['description']}"
                for f in severe_findings
            ])

            user_prompt = (
                f"Language: {lang}\n"
                f"File: {file_path}\n\n"
                f"Detected Findings:\n{findings_context}\n\n"
                f"Source Code:\n{code}"
            )

            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content=user_prompt),
            ]

            report = structured_llm.invoke(messages)
            
            # Map Pydantic schema to dict representation
            suggestions = []
            for s in report.suggestions:
                suggestions.append({
                    "finding_title": s.finding_title,
                    "line_start": s.line_start,
                    "line_end": s.line_end,
                    "original_code": s.original_code,
                    "corrected_code": s.corrected_code,
                    "explanation": s.explanation,
                    "is_ai_generated": True,
                })
            
            logger.info("AI Auto-Fix generated %d refactoring suggestions.", len(suggestions))
            return {"fix_suggestions": suggestions}

        except Exception as exc:
            logger.warning("AI Auto-Fix failed: %s. Falling back to template rules.", exc)

    # 2. Fallback: Rule-based template fixes
    try:
        suggestions = []
        lines = code.splitlines()

        for f in severe_findings:
            line_start = f.get("line_start", 1)
            line_end = f.get("line_end", line_start)
            rule_id = f.get("rule_id", "")
            title = f.get("title", "Security Vulnerability")

            # Extract original code snippet safely
            orig_start = max(0, line_start - 1)
            orig_end = min(len(lines), line_end)
            original_snippet = "\n".join(lines[orig_start:orig_end])

            corrected = ""
            explanation = ""

            # Check Rule Templates
            if rule_id == "SEC-HARDCODED-SECRET":
                # Extract variable name from snippet (e.g. "api_key = ...")
                var_name = "api_key"
                if "=" in original_snippet:
                    var_name = original_snippet.split("=")[0].strip().split()[-1]

                if lang.lower() in ("python", "py"):
                    corrected = f"import os\n{var_name} = os.environ.get(\"{var_name.upper()}\")"
                    explanation = "Replaced hardcoded string assignment with a secure environment variable lookup using 'os.environ.get()'."
                else:
                    corrected = f"const {var_name} = process.env.{var_name.upper()};"
                    explanation = "Replaced hardcoded string assignment with Node.js environment lookup using 'process.env'."
            
            elif rule_id == "SEC-SQL-INJECTION":
                if lang.lower() in ("python", "py"):
                    corrected = "# Use parameterized queries\nquery = \"SELECT * FROM users WHERE id = %s\"\ndb.execute(query, (user_id,))"
                    explanation = "Replaced unsafe dynamic string interpolation in SQL query with parameterized placeholder syntax (%s) to prevent SQL Injection."
                else:
                    corrected = "// Use prepared / parameterized query\nconst sql = 'SELECT * FROM data WHERE name = ?';\ndb.query(sql, [input]);"
                    explanation = "Replaced unsafe template literal interpolation in SQL query with placeholder query parameters (?) to prevent SQL Injection."
            
            elif rule_id == "SEC-UNSAFE-EXECUTION":
                corrected = "# Avoid eval/exec execution. Use explicit parser or safe mapping APIs."
                explanation = "Unsafe dynamix evaluation calls (like eval/exec) were replaced with guidance comments to implement safe static business logic mappings."
            
            if corrected:
                suggestions.append({
                    "finding_title": title,
                    "line_start": line_start,
                    "line_end": line_end,
                    "original_code": original_snippet,
                    "corrected_code": corrected,
                    "explanation": explanation,
                    "is_ai_generated": False,
                })

        logger.info("Static Fallback Auto-Fix generated %d suggestions.", len(suggestions))
        return {"fix_suggestions": suggestions}
    except Exception as exc:
        logger.error("Static auto-fix fallback failed: %s", exc)
        return {"fix_suggestions": []}
