"""
Plexus Backend — Git Service

Handles repository retrieval and workspace operations using GitPython,
providing temporary directory setups and Windows-resilient file cleanups.
"""

from __future__ import annotations

import logging
import os
import shutil
import stat
import tempfile
from uuid import UUID

import git

logger = logging.getLogger(__name__)


def _remove_readonly(func, path, excinfo) -> None:
    """Error handler for shutil.rmtree to clean read-only files on Windows.

    Windows often blocks rmtree on .git internal files due to write protections.
    """
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as exc:
        logger.warning("Failed to force delete path %s: %s", path, exc)


class GitService:
    """Service for managing local clones of Git repositories."""

    # ------------------------------------------------------------------
    # Clone
    # ------------------------------------------------------------------

    def clone_repo(
        self,
        clone_url: str,
        branch: str | None = None,
    ) -> str:
        """Clones a remote repository to a new temporary local directory.

        Args:
            clone_url: Remote clone URL (HTTPS).
            branch: Optional branch name. If omitted, default branch is cloned.

        Returns:
            The absolute path of the local clone directory.

        Raises:
            git.GitCommandError: If cloning fails.
        """
        temp_dir = tempfile.mkdtemp(prefix="plexus_scan_")
        logger.info("Cloning repo %s into temp folder %s", clone_url, temp_dir)

        clone_kwargs = {}
        if branch:
            clone_kwargs["branch"] = branch

        try:
            # Performs the remote clone operation
            git.Repo.clone_from(clone_url, temp_dir, **clone_kwargs)
            logger.info("Clone completed successfully for %s", clone_url)
            return temp_dir
        except Exception as exc:
            logger.error("Failed to clone %s: %s", clone_url, exc)
            self.cleanup_repo(temp_dir)
            raise exc

    # ------------------------------------------------------------------
    # Commit details
    # ------------------------------------------------------------------

    def get_latest_commit_sha(self, repo_path: str) -> str | None:
        """Gets the HEAD commit SHA for the current checkout directory.

        Args:
            repo_path: Absolute local path to the cloned repository.

        Returns:
            The full 40-character commit SHA, or None if error.
        """
        try:
            with git.Repo(repo_path) as repo:
                return repo.head.commit.hexsha
        except Exception as exc:
            logger.error("Failed to read HEAD commit SHA from %s: %s", repo_path, exc)
            return None

    def get_commit_metadata(self, repo_path: str, commit_sha: str) -> dict | None:
        """Retrieves details of a specific commit.

        Args:
            repo_path: Local repository path.
            commit_sha: Full or short commit SHA.

        Returns:
            A dictionary of commit details (message, author, date, sha).
        """
        try:
            with git.Repo(repo_path) as repo:
                commit = repo.commit(commit_sha)
                return {
                    "sha": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "author_email": commit.author.email,
                    "timestamp": commit.committed_datetime,
                }
        except Exception as exc:
            logger.error("Failed to read metadata for commit %s in %s: %s", commit_sha, repo_path, exc)
            return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup_repo(self, repo_path: str) -> None:
        """Removes the local cloned repository workspace directory.

        Frees up disk space and handles read-only lock overrides.

        Args:
            repo_path: Path to clean up.
        """
        if not repo_path or not os.path.exists(repo_path):
            return

        logger.info("Cleaning up local clone workspace at %s", repo_path)
        try:
            shutil.rmtree(repo_path, onerror=_remove_readonly)
            logger.info("Cleanup completed for %s", repo_path)
        except Exception as exc:
            logger.error("Failed to cleanup directory %s: %s", repo_path, exc)
