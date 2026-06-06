"""
Plexus Backend — Code Review Agent

AI agent responsible for reviewing source code for maintainability, style
conventions, complexity, and best practices using ChatOpenAI.
Includes a static code style fallback for offline execution.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured Output Schema (Pydantic)
# ---------------------------------------------------------------------------

class ReviewCommentSchema(BaseModel):
    """Structured representation of a single code review comment."""

    title: str = Field(..., description="Summary of the quality/style issue, e.g. 'Long Function'.")
    description: str = Field(..., description="Detailed explanation of why the code could be improved.")
    line: int = Field(..., ge=1, description="Line number of the review comment.")
    severity: str = Field(
        ...,
        description="Review severity — must be one of: 'error', 'warning', 'info'.",
    )
    suggestion: str = Field(..., description="Actionable suggestion or refactored code example.")


class CodeReviewReportSchema(BaseModel):
    """Unified collection of code review comments returned by the model."""

    comments: list[ReviewCommentSchema] = Field(
        default_factory=list,
        description="Collection of code quality review comments.",
    )


# ---------------------------------------------------------------------------
# Agent Node Function
# ---------------------------------------------------------------------------

def code_review_agent_node(state: AgentState) -> dict[str, any]:
    """LangGraph node representing the Code Review Agent.

    Inspects code using GPT models to find style and maintainability concerns,
    falling back to static styling rules if offline or missing API keys.
    """
    logger.info("Executing Code Review Agent node for file: %s", state.get("file_path"))
    
    code = state.get("code_content", "")
    lang = state.get("language", "")
    file_path = state.get("file_path", "")

    # 1. Try AI Analysis if key is available
    if settings.openai_api_key:
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                openai_api_key=settings.openai_api_key,
            )
            structured_llm = llm.with_structured_output(CodeReviewReportSchema)

            system_instruction = (
                "You are an expert code reviewer. Review the provided source code "
                "for readability, maintainability, optimization, and standard style "
                "conventions (e.g. PEP 8 for Python, ES6 guidelines for JavaScript). "
                "Look for complex nested loops, excessively long functions, missing "
                "error handling, or redundant code. "
                "Be extremely precise. Give accurate line numbers. "
                "Provide helpful refactored snippets inside suggestions."
            )
            user_prompt = f"Language: {lang}\nFile: {file_path}\n\nCode Content:\n{code}"

            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content=user_prompt),
            ]

            report = structured_llm.invoke(messages)
            
            # Map Pydantic schema to dict representation
            comments = []
            for c in report.comments:
                comments.append({
                    "title": c.title,
                    "description": c.description,
                    "line": c.line,
                    "severity": c.severity.lower(),
                    "suggestion": c.suggestion,
                    "is_ai_generated": True,
                })
            
            logger.info("AI Code Review completed with %d comments.", len(comments))
            return {"review_comments": comments}

        except Exception as exc:
            logger.warning("AI Code Review failed: %s. Falling back to static styling checks.", exc)

    # 2. Fallback: Run static styling checks
    try:
        comments = []
        lines = code.splitlines()
        
        # Check for style and comment rules
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()

            # Rule A: Line length check (> 100 chars)
            if len(line) > 100 and not stripped.startswith(("import", "from")):
                comments.append({
                    "title": "Line Too Long",
                    "description": f"Line exceeds 100 characters ({len(line)} chars). Keep lines under 100 characters for readability.",
                    "line": line_num,
                    "severity": "info",
                    "suggestion": "Break the line down into multiple lines or extract complex sub-expressions.",
                    "is_ai_generated": False,
                })

            # Rule B: Unresolved TODO/FIXME comments
            if any(term in stripped.upper() for term in ("TODO:", "TODO ", "FIXME:", "FIXME ")):
                comments.append({
                    "title": "Unresolved Task Tracker",
                    "description": f"Comment contains an unresolved task indicator: '{stripped}'.",
                    "line": line_num,
                    "severity": "warning",
                    "suggestion": "Implement the missing logic or register a task ticket, then clear the comment.",
                    "is_ai_generated": False,
                })

        # Rule C: Python missing function/class docstrings
        if lang.lower() in ("python", "py"):
            # Simple regex search for functions and class declarations
            func_decl_matches = re.finditer(r"^\s*def\s+(\w+)\s*\(", code, re.MULTILINE)
            for m in func_decl_matches:
                func_name = m.group(1)
                if func_name.startswith("_"):
                    continue
                # Determine definition line number
                char_idx = m.start()
                line_idx = code[:char_idx].count("\n") + 1
                
                # Check if next non-empty line starts with triple quotes
                # Very simple heuristic
                remaining_code = code[m.end():]
                clean_rem = remaining_code.strip()
                if not (clean_rem.startswith('"""') or clean_rem.startswith("'''")):
                    comments.append({
                        "title": "Missing Docstring",
                        "description": f"Public function '{func_name}' is missing a docstring explaining its behavior.",
                        "line": line_idx,
                        "severity": "info",
                        "suggestion": f"Add a PEP-257 docstring explaining arguments, return values, and behavior of '{func_name}'.",
                        "is_ai_generated": False,
                    })

        logger.info("Static Style Scan completed with %d comments.", len(comments))
        return {"review_comments": comments}
    except Exception as exc:
        logger.error("Static review scanner fallback failed: %s", exc)
        return {"review_comments": []}
