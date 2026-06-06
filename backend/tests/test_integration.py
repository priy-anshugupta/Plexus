"""
Plexus Backend — Integration & Unit Tests

Runs test validation suites checking code remediation, GitHub PR mock pipelines,
and prompt routing algorithms.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from app.services.github_service import GithubService
from app.services.remediation_service import RemediationService
from app.services.privacy_service import PrivacyService


class TestRemediationService(unittest.TestCase):
    """Checks file replacement and compilation check hooks."""

    def setUp(self):
        self.service = RemediationService()
        self.temp_dir = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_dir, "sample.py")

        # Create sample file containing mock vulnerable code
        self.sample_code = (
            "import os\n"
            "def handle_query(user_input):\n"
            "    # Vulnerable format string\n"
            "    query = f\"SELECT * FROM items WHERE name = '{user_input}'\"\n"
            "    print(query)\n"
            "    return True\n"
        )
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.sample_code)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_apply_remediation_success(self):
        """Checks replacing a range of lines with corrected syntax."""
        new_snippet = (
            "    # Correct: Use bind parameters\n"
            "    query = \"SELECT * FROM items WHERE name = %s\"\n"
            "    params = (user_input,)\n"
            "    print(query, params)"
        )
        # We replace line 4 (index 4)
        success = self.service.apply_remediation(
            self.file_path, start_line=4, end_line=4, new_code=new_snippet
        )
        self.assertTrue(success)

        # Read back content and verify replacement
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Use bind parameters", content)
        self.assertIn("params = (user_input,)", content)
        self.assertNotIn("f\"SELECT * FROM items", content)

    def test_apply_remediation_syntax_failure(self):
        """Checks that applying broken syntax triggers rollbacks."""
        broken_snippet = "    query = f\"SELECT * FROM items WHERE name = '{"
        
        # Replace line 4 with incomplete brackets (syntax error)
        success = self.service.apply_remediation(
            self.file_path, start_line=4, end_line=4, new_code=broken_snippet
        )
        self.assertFalse(success)

        # Verify file restored to original code
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, self.sample_code)


class TestPrivacyService(unittest.TestCase):
    """Validates prompt PII and secret detection rules."""

    def setUp(self):
        self.service = PrivacyService()

    def test_contains_sensitive_data(self):
        # Email checks
        self.assertTrue(self.service.contains_sensitive_data("Contact test@example.com for queries"))
        # AWS Key check (requires AWS access key prefix keyword + 40-char key context)
        self.assertTrue(self.service.contains_sensitive_data("AWS access keys AKIAIOSFODNN7EXAMPLE and secret is aws_key_secret: 1234567890123456789012345678901234567890"))
        # Private key check
        self.assertTrue(self.service.contains_sensitive_data("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAA\n-----END RSA PRIVATE KEY-----"))
        
        # Non-sensitive check
        self.assertFalse(self.service.contains_sensitive_data("What does standard REST API response format look like?"))

    def test_mask_sensitive_data(self):
        text = "My email is support@plexus.com and phone is 555-666-7777."
        masked = self.service.mask_sensitive_data(text)
        self.assertIn("[MASKED_EMAIL]", masked)
        self.assertIn("[MASKED_PHONE]", masked)
        self.assertNotIn("support@plexus.com", masked)

    def test_get_llm_routing_endpoint(self):
        # Sensitive routes locally
        route_local = self.service.get_llm_routing_endpoint("Check this API Key: key_secret = '1234567890123456789012345678901234567890'")
        self.assertEqual(route_local["provider"], "local")
        self.assertEqual(route_local["model"], "llama3")

        # Non-sensitive routes to cloud
        route_cloud = self.service.get_llm_routing_endpoint("How can I parse AST nodes using tree-sitter?")
        self.assertEqual(route_cloud["provider"], "cloud")
        self.assertEqual(route_cloud["model"], "gpt-4o")


class TestGithubService(unittest.TestCase):
    """Checks PR and branch helpers."""

    def setUp(self):
        self.service = GithubService()

    def test_parse_repo_slug(self):
        url = "https://github.com/priy-anshugupta/Plexus.git"
        slug = self.service._parse_repo_slug(url)
        self.assertEqual(slug, "priy-anshugupta/Plexus")


if __name__ == "__main__":
    unittest.main()
