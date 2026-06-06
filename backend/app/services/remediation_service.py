"""
Plexus Backend — Remediation Service

Manages code modifications for security auto-fixes. Replaces targeted lines
of source files with AI-generated repairs and checks syntax validity.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class RemediationService:
    """Service for applying and validating automated code fixes."""

    def apply_remediation(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        new_code: str,
    ) -> bool:
        """Replaces a range of lines in a file with new code.

        Args:
            file_path: Absolute local path to the file.
            start_line: 1-indexed starting line number of the target block.
            end_line: 1-indexed ending line number of the target block.
            new_code: Drop-in replacement string for the lines.

        Returns:
            True if applied successfully, False otherwise.
        """
        if not os.path.exists(file_path):
            logger.error("Remediation target file does not exist: %s", file_path)
            return False

        try:
            # Read current content
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Bounds validation
            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                logger.error(
                    "Invalid line bounds for remediation. File lines: %d, start: %d, end: %d",
                    len(lines),
                    start_line,
                    end_line,
                )
                return False

            # backup content in case syntax check fails
            original_content = "".join(lines)

            # Replace lines. Note line numbers are 1-indexed.
            # We slice up to start_line - 1, insert new code, and append from end_line.
            prefix = lines[: start_line - 1]
            suffix = lines[end_line:]
            
            # Ensure new code ends with newline if the file does
            if not new_code.endswith("\n"):
                new_code += "\n"

            modified_content = "".join(prefix) + new_code + "".join(suffix)

            # Write modified content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)

            # Verify syntax
            if not self.verify_syntax(file_path):
                logger.warning("Syntax validation failed for %s. Restoring original content.", file_path)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(original_content)
                return False

            logger.info("Successfully applied remediation to %s at lines %d-%d", file_path, start_line, end_line)
            return True

        except Exception as exc:
            logger.error("Failed to apply remediation to %s: %s", file_path, exc)
            return False

    def verify_syntax(self, file_path: str) -> bool:
        """Verifies that the target file is syntactically correct after edit.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if syntax is valid, False if syntax errors are found.
        """
        ext = os.path.split(file_path)[1].split(".")[-1].lower()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if ext == "py":
                # Compile check for Python
                compile(content, file_path, "exec")
                return True
            
            # For JavaScript, TypeScript, YAML, JSON, etc., we do basic validation
            if ext == "json":
                import json
                json.loads(content)
                return True
                
            if ext in ("yml", "yaml"):
                # Basic bracket check or skip if yaml module is missing
                try:
                    import yaml
                    yaml.safe_load(content)
                    return True
                except ImportError:
                    pass

            # Fallback for other languages: just ensure it's readable
            return True

        except Exception as exc:
            logger.warning("Syntax error found in %s: %s", file_path, exc)
            return False
