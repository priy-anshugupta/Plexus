"""
Plexus Backend — Privacy Router Service

Detects credentials, PII (Personally Identifiable Information), and secrets
in LLM prompts, routing sensitive requests to local air-gapped endpoints.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Heuristics/regex match patterns for PII & Credentials
PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b\d{3}-\d{3}-\d{4}\b"),
    "aws_access_key": re.compile(r"\b(AKIA|ASCA|ASIA)[A-Z0-9]{16}\b"),
    "aws_secret_key": re.compile(r"\b[A-Za-z0-9/+=]{40}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    "slack_webhook": re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9_]+"),
    "generic_secret": re.compile(r"(api[-_]?key|secret[-_]?key|password|db[-_]?url|connection[-_]?string)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE),
}


class PrivacyService:
    """Service for PII/Secret detection and privacy-based LLM routing."""

    def contains_sensitive_data(self, text: str) -> bool:
        """Checks if a text snippet contains credentials or PII.

        Args:
            text: Input string (e.g. prompt or code snippet).

        Returns:
            True if sensitive patterns are detected, False otherwise.
        """
        for name, pattern in PATTERNS.items():
            # Special check for aws_secret_key: since it matches any 40 character string,
            # we check if it is nearby context terms like 'secret', 'aws', 'key', or 'key_secret'
            # to prevent false positives on random 40-char hashes.
            if name == "aws_secret_key":
                matches = pattern.findall(text)
                if matches:
                    lower_text = text.lower()
                    if any(term in lower_text for term in ["aws", "secret", "credentials", "access"]):
                        logger.info("Sensitive data detected: potential AWS Secret Key")
                        return True
                    continue

            if pattern.search(text):
                logger.info("Sensitive data detected: potential %s pattern match", name)
                return True

        return False

    def mask_sensitive_data(self, text: str) -> str:
        """Replaces sensitive patterns in the text with masked placeholders.

        Args:
            text: Input string.

        Returns:
            Sanitized string with masked details.
        """
        sanitized = text
        for name, pattern in PATTERNS.items():
            if name == "aws_secret_key":
                # Only mask if it is in a context that looks like an AWS key
                if any(term in text.lower() for term in ["aws", "secret", "credentials"]):
                    sanitized = pattern.sub("[MASKED_AWS_SECRET_KEY]", sanitized)
                continue
            sanitized = pattern.sub(f"[MASKED_{name.upper()}]", sanitized)

        return sanitized

    def get_llm_routing_endpoint(self, text: str) -> dict[str, str]:
        """Evaluates prompt content and returns the appropriate LLM route config.

        Routes sensitive queries to local models (e.g., Ollama/vLLM) and non-sensitive
        queries to the primary cloud service (e.g. OpenAI).
        """
        if self.contains_sensitive_data(text):
            logger.info("Routing LLM request locally: Sensitive data detected.")
            return {
                "provider": "local",
                "endpoint": "http://localhost:11434/v1",  # Local Ollama default
                "model": "llama3",
                "reason": "Contains sensitive patterns or credentials.",
            }
        else:
            logger.info("Routing LLM request to cloud: Non-sensitive data.")
            return {
                "provider": "cloud",
                "endpoint": "https://api.openai.com/v1",
                "model": "gpt-4o",
                "reason": "Clean input query.",
            }
