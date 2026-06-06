"""
Plexus Backend — Scanner Service

Orchestrates the entire scanning pipeline: workspace cloning, AST parsing,
executing security/quality detection rules, and persisting findings to the database.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from uuid import UUID

from app.core.database import db_manager
from app.models.finding import Finding, FindingCategory, FindingStatus, Severity
from app.models.scan import Scan, ScanStatus
from app.services.git_service import GitService
from app.services.parser_service import ParserService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ScannerService:
    """Service to orchestrate and run security scans on code repositories."""

    def __init__(self) -> None:
        self._git_service = GitService()
        self._parser_service = ParserService()

        # Simple regex for hardcoded secret detection on raw strings
        self._secret_patterns = [
            re.compile(r"api[-_]?key", re.IGNORECASE),
            re.compile(r"secret", re.IGNORECASE),
            re.compile(r"token", re.IGNORECASE),
            re.compile(r"password", re.IGNORECASE),
            re.compile(r"private[-_]?key", re.IGNORECASE),
        ]

    # ------------------------------------------------------------------
    # Core Scan Orchestrator
    # ------------------------------------------------------------------

    def run_scan(self, scan_id: UUID) -> None:
        """Executes a code scan asynchronously.

        Fetches the scan target, clones the workspace, scans all code files
        via the AST parsing engine, records findings, and cleans up the temp dir.

        Args:
            scan_id: UUID of the Scan record to run.
        """
        # We open a new dedicated DB session for the background worker thread
        with db_manager.get_db_session() as db:
            scan = db.get(Scan, scan_id)
            if not scan:
                logger.error("Scan job %s not found in DB.", scan_id)
                return

            repo_record = scan.repository
            if not repo_record:
                logger.error("Repository not associated with scan %s.", scan_id)
                scan.status = ScanStatus.FAILED
                scan.error_message = "Associated repository not found."
                db.commit()
                return

            # 1. Update state to RUNNING
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            db.commit()
            logger.info("Scan %s started running on repo %s", scan_id, repo_record.full_name)

            temp_dir = None
            try:
                # 2. Clone repository to temp folder
                temp_dir = self._git_service.clone_repo(
                    clone_url=repo_record.clone_url,
                    branch=scan.branch,
                )

                # Capture actual commit SHA if not specified
                latest_sha = self._git_service.get_latest_commit_sha(temp_dir)
                if not scan.commit_sha and latest_sha:
                    scan.commit_sha = latest_sha
                    db.commit()

                # 3. Walk through local cloned directory and analyze files
                findings_found: list[Finding] = []
                for root, _, files in os.walk(temp_dir):
                    # Skip hidden directories like .git
                    if ".git" in root.split(os.sep):
                        continue

                    for file in files:
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext not in (".py", ".js", ".jsx", ".ts", ".tsx"):
                            continue

                        full_path = os.path.join(root, file)
                        # Derive relative file path inside repository
                        relative_path = os.path.relpath(full_path, temp_dir)

                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                code_content = f.read()

                            lang = "python" if file_ext == ".py" else "javascript"
                            file_findings = self._analyze_file(
                                relative_path=relative_path,
                                code_content=code_content,
                                language=lang,
                                scan_id=scan.id,
                                repo_id=repo_record.id,
                            )
                            findings_found.extend(file_findings)
                        except Exception as exc:
                            logger.warning("Failed to scan file %s: %s", relative_path, exc)

                # 4. Save findings to PostgreSQL
                for f in findings_found:
                    db.add(f)
                db.flush()

                # 5. Complete Scan metadata
                now = datetime.utcnow()
                scan.status = ScanStatus.COMPLETED
                scan.completed_at = now
                if scan.started_at:
                    scan.duration_seconds = (now - scan.started_at).total_seconds()
                scan.total_findings = len(findings_found)
                
                # Update repository's last_scanned_at
                repo_record.last_scanned_at = now
                
                db.commit()
                logger.info(
                    "Scan %s completed successfully. %d findings recorded.",
                    scan.id,
                    len(findings_found),
                )

            except Exception as exc:
                logger.exception("Error executing scan %s: %s", scan_id, exc)
                db.rollback()
                # Mark scan as failed
                scan.status = ScanStatus.FAILED
                scan.completed_at = datetime.utcnow()
                if scan.started_at:
                    scan.duration_seconds = (scan.completed_at - scan.started_at).total_seconds()
                scan.error_message = str(exc)
                db.commit()

            finally:
                # 6. Cleanup clone directory workspace
                if temp_dir:
                    self._git_service.cleanup_repo(temp_dir)

    # ------------------------------------------------------------------
    # File Analyzer & Rules Engine
    # ------------------------------------------------------------------

    def _analyze_file(
        self,
        relative_path: str,
        code_content: str,
        language: str,
        scan_id: UUID,
        repo_id: UUID,
    ) -> list[Finding]:
        """Analyzes a single source code file using the AST parser.

        Checks code against static security and quality rules.
        """
        findings: list[Finding] = []
        
        # Call tree-sitter to parse code and extract nodes
        ast_data = self._parser_service.parse_code(code_content, language)

        # Split lines for snippet extraction
        lines = code_content.splitlines()

        # Helper to get snippet lines
        def get_snippet(start: int, end: int | None = None) -> str:
            start_idx = max(0, start - 1)
            end_idx = min(len(lines), (end or start))
            return "\n".join(lines[start_idx:end_idx])

        # --- Rule 1: Hardcoded Secrets & Credentials ---
        for assign in ast_data.get("assignments", []):
            var_name = assign.get("variable", "")
            val_text = assign.get("value", "").strip()
            line = assign.get("line", 1)

            # Check if variable name matches any secret keys
            if any(pat.search(var_name) for pat in self._secret_patterns):
                # Verify if assigned value is a hardcoded string literal
                # e.g., "secret_value", 'secret_value', f"secret", but NOT variable names/function calls
                is_string_literal = (
                    (val_text.startswith('"') and val_text.endswith('"')) or
                    (val_text.startswith("'") and val_text.endswith("'"))
                )
                # Strip quotes and check if it's not a placeholder
                clean_val = val_text.strip("'\"")
                is_placeholder = clean_val.lower() in ("placeholder", "true", "false", "null", "none", "", "env")
                
                if is_string_literal and not is_placeholder and len(clean_val) > 4:
                    findings.append(
                        Finding(
                            scan_id=scan_id,
                            repository_id=repo_id,
                            file_path=relative_path,
                            line_start=line,
                            line_end=line,
                            severity=Severity.HIGH,
                            category=FindingCategory.SECURITY,
                            status=FindingStatus.OPEN,
                            title="Hardcoded Credential Detected",
                            description=(
                                f"Variable '{var_name}' appears to be assigned a hardcoded password or credential key: "
                                f"{val_text}."
                            ),
                            suggestion="Move secrets and credentials to environment variables or use a secret manager.",
                            code_snippet=get_snippet(line),
                            rule_id="SEC-HARDCODED-SECRET",
                            confidence_score=0.85,
                            is_ai_generated=False,
                        )
                    )

        # --- Rule 2: SQL Injection Risk ---
        # We check both variable assignments (where queries are built) and execute/query calls
        
        # 2a. Check variable assignments
        for assign in ast_data.get("assignments", []):
            var_name = assign.get("variable", "").lower()
            val_text = assign.get("value", "")
            line = assign.get("line", 1)

            # Check if variable name looks like query or sql, and it contains SQL keywords
            is_query_var = any(term in var_name for term in ("sql", "query", "stmt", "command"))
            is_sql_query = any(keyword in val_text.upper() for keyword in ("SELECT", "INSERT", "UPDATE", "DELETE", "WHERE"))
            
            if language == "python":
                has_interpolation = ("f\"" in val_text or "f'" in val_text or ".format(" in val_text or " + " in val_text or " % " in val_text)
            else:
                has_interpolation = ("`" in val_text and "${" in val_text) or (" + " in val_text)

            if is_sql_query and has_interpolation and (is_query_var or len(val_text) < 500):
                findings.append(
                    Finding(
                        scan_id=scan_id,
                        repository_id=repo_id,
                        file_path=relative_path,
                        line_start=line,
                        line_end=line,
                        severity=Severity.CRITICAL,
                        category=FindingCategory.SECURITY,
                        status=FindingStatus.OPEN,
                        title="Potential SQL Injection Vulnerability",
                        description=(
                            f"SQL query string is constructed with dynamic interpolation or concatenation in assignment to '{assign.get('variable')}': "
                            f"{val_text}."
                        ),
                        suggestion="Use parameterized queries / prepared statements instead of directly concatenating strings in SQL queries.",
                        code_snippet=get_snippet(line),
                        rule_id="SEC-SQL-INJECTION",
                        confidence_score=0.85,
                        is_ai_generated=False,
                    )
                )

        # 2b. Check execute/query calls directly
        for call in ast_data.get("calls", []):
            func_name = call.get("function_name", "")
            text = call.get("text", "")
            line = call.get("line", 1)

            # Look for typical database execute methods
            if any(term in func_name.lower() for term in ("execute", "query", "rawsql", "select")):
                if language == "python":
                    has_interpolation = ("f\"" in text or "f'" in text or ".format(" in text or " + " in text or " % " in text)
                else:
                    has_interpolation = ("`" in text and "${" in text) or (" + " in text)

                is_sql_query = any(keyword in text.upper() for keyword in ("SELECT", "INSERT", "UPDATE", "DELETE", "WHERE"))

                if has_interpolation and is_sql_query:
                    # Prevent double-flagging on the same line if already flagged by assignment check
                    already_flagged = any(f.line_start == line and f.rule_id == "SEC-SQL-INJECTION" for f in findings)
                    if not already_flagged:
                        findings.append(
                            Finding(
                                scan_id=scan_id,
                                repository_id=repo_id,
                                file_path=relative_path,
                                line_start=line,
                                line_end=line,
                                severity=Severity.CRITICAL,
                                category=FindingCategory.SECURITY,
                                status=FindingStatus.OPEN,
                                title="Potential SQL Injection Vulnerability",
                                description=(
                                    f"SQL execution method '{func_name}' is invoked with dynamic string interpolation or concatenation: "
                                    f"{text}."
                                ),
                                suggestion="Use parameterized queries / prepared statements instead of directly concatenating strings in SQL queries.",
                                code_snippet=get_snippet(line),
                                rule_id="SEC-SQL-INJECTION",
                                confidence_score=0.90,
                                is_ai_generated=False,
                            )
                        )

        # --- Rule 3: Unsafe Execution (eval/exec/shell execution) ---
        for call in ast_data.get("calls", []):
            func_name = call.get("function_name", "")
            text = call.get("text", "")
            line = call.get("line", 1)

            # Split function path to get leaf name (e.g. 'db.execute' -> 'execute')
            parts = func_name.lower().split(".")
            leaf_name = parts[-1] if parts else ""

            # Unsafe methods
            unsafe_full = ("os.system", "subprocess.popen", "execsync", "spawnsync")
            unsafe_leaf = ("eval", "exec")

            is_unsafe = (
                func_name.lower() in unsafe_full or
                leaf_name in unsafe_leaf or
                any(uf in func_name.lower() for uf in ("subprocess.popen", "execsync", "spawnsync"))
            )

            if is_unsafe:
                findings.append(
                    Finding(
                        scan_id=scan_id,
                        repository_id=repo_id,
                        file_path=relative_path,
                        line_start=line,
                        line_end=line,
                        severity=Severity.CRITICAL,
                        category=FindingCategory.SECURITY,
                        status=FindingStatus.OPEN,
                        title="Unsafe Shell or Dynamic Code Execution",
                        description=f"Invocation of unsafe dynamic execution function '{func_name}': {text}.",
                        suggestion="Avoid dynamic shell command or code execution. Use safer APIs or libraries.",
                        code_snippet=get_snippet(line),
                        rule_id="SEC-UNSAFE-EXECUTION",
                        confidence_score=0.95,
                        is_ai_generated=False,
                    )
                )

        return findings
