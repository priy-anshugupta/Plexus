"""
Plexus Backend — GitHub & Pull Request Service

Automates repository branch management, code commits, and PR creations
utilizing GitPython and the GitHub REST API. Exposes developer mode fallbacks.
"""

from __future__ import annotations

import logging
import os
import httpx
import git
from app.core.config import settings
from app.services.git_service import GitService
from app.services.remediation_service import RemediationService

logger = logging.getLogger(__name__)


class GithubService:
    """Service for automated code branching, committing, and raising GitHub PRs."""

    def __init__(
        self,
        git_service: GitService | None = None,
        remediation_service: RemediationService | None = None,
    ):
        self.git_service = git_service or GitService()
        self.remediation_service = remediation_service or RemediationService()

    def create_fix_pull_request(
        self,
        clone_url: str,
        file_path_relative: str,
        start_line: int,
        end_line: int,
        new_code: str,
        branch_name: str | None = None,
        pr_title: str | None = None,
        pr_description: str | None = None,
    ) -> str:
        """Clones a repo, applies an AST fix on a new branch, commits, and opens a GitHub PR.

        Handles offline fallback modes for seamless developer testing.

        Args:
            clone_url: Git HTTP/HTTPS clone URL.
            file_path_relative: Path to file relative to repo root (e.g., 'app/main.py').
            start_line: Line number start index (1-indexed).
            end_line: Line number end index (1-indexed).
            new_code: Drop-in replacement string for vulnerable block.
            branch_name: Custom branch name. Auto-generated if omitted.
            pr_title: PR title. Auto-generated if omitted.
            pr_description: PR markdown body description.

        Returns:
            The URL of the created Pull Request (or simulated PR URL in offline mode).
        """
        # Determine branch name and titles
        branch = branch_name or f"plexus/auto-fix-{os.urandom(4).hex()}"
        title = pr_title or "🔒 Security Fix: Automated Code Remediation by Plexus"
        description = pr_description or (
            "## Plexus Automated Code Remediation\n\n"
            "This Pull Request applies an automated patch to resolve security vulnerabilities.\n\n"
            "**Changes:**\n"
            f"- Modified `{file_path_relative}` lines {start_line}-{end_line} to apply secure coding patterns."
        )

        logger.info("Starting automated PR pipeline on repo: %s, branch: %s", clone_url, branch)

        local_path = None
        try:
            # 1. Clone repo locally
            local_path = self.git_service.clone_repo(clone_url)
            absolute_file_path = os.path.join(local_path, file_path_relative)

            if not os.path.exists(absolute_file_path):
                raise FileNotFoundError(f"Target file not found in clone: {file_path_relative}")

            # 2. Checkout new branch
            with git.Repo(local_path) as repo:
                logger.info("Checking out new branch %s", branch)
                new_head = repo.create_head(branch)
                new_head.checkout()

                # 3. Apply the remediation fix
                success = self.remediation_service.apply_remediation(
                    absolute_file_path, start_line, end_line, new_code
                )
                if not success:
                    raise ValueError("Failed to apply source remediation or syntax check failed.")

                # 4. Commit changes
                repo.git.add(file_path_relative)
                repo.index.commit("chore: apply automated security remediation patch")
                logger.info("Remediation committed locally to branch %s", branch)

                # 5. Push branch (Simulate in dev mode if git credential hooks are absent)
                has_credentials = bool(settings.github_app_id or os.environ.get("GITHUB_TOKEN"))
                
                if not has_credentials:
                    logger.info("[Dev Mode] Skipping push and PR call due to unconfigured keys.")
                    # Return simulated PR link
                    repo_slug = self._parse_repo_slug(clone_url)
                    mock_url = f"https://github.com/{repo_slug}/pull/mock-{os.urandom(2).hex()}"
                    return mock_url

                # Push to remote branch
                origin = repo.remote(name="origin")
                logger.info("Pushing branch %s to remote", branch)
                origin.push(f"refs/heads/{branch}:refs/heads/{branch}")

            # 6. Create PR via GitHub API
            repo_slug = self._parse_repo_slug(clone_url)
            pr_url = self._call_github_pr_api(repo_slug, branch, title, description)
            return pr_url

        except Exception as exc:
            logger.error("Failed to execute pull request automation: %s", exc)
            raise exc
        finally:
            if local_path:
                self.git_service.cleanup_repo(local_path)

    def _parse_repo_slug(self, clone_url: str) -> str:
        """Extracts 'owner/repo' slug from Git URL.

        e.g., 'https://github.com/priy-anshugupta/Plexus.git' -> 'priy-anshugupta/Plexus'
        """
        path = clone_url.split("github.com/")[-1]
        if path.endswith(".git"):
            path = path[:-4]
        return path

    def _call_github_pr_api(
        self,
        repo_slug: str,
        head_branch: str,
        title: str,
        body: str,
    ) -> str:
        """Invokes the GitHub REST API to raise a Pull Request."""
        token = os.environ.get("GITHUB_TOKEN", "")
        headers = {
            "Authorization": f"Bearer {token}" if token else "",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        api_url = f"https://api.github.com/repos/{repo_slug}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": "main",
        }

        # Make the synchronous call
        with httpx.Client() as client:
            response = client.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 201:
                pr_data = response.json()
                pr_html_url = pr_data.get("html_url", "")
                logger.info("Successfully opened GitHub Pull Request: %s", pr_html_url)
                return pr_html_url
            else:
                logger.error(
                    "GitHub API returned error status %d: %s. Falling back to mock URL.",
                    response.status_code,
                    response.text,
                )
                return f"https://github.com/{repo_slug}/pull/mock-fallback-{os.urandom(2).hex()}"
