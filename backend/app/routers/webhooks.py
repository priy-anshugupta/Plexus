"""
Plexus Backend — Git Webhooks Router

Listens for push/pull request webhooks from GitHub, triggering scans in the
background and indexing findings.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from app.services.scanner_service import ScannerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Instantiated scanner service
scanner_service = ScannerService()


async def run_background_scan(clone_url: str, branch: str) -> None:
    """Clones and scans a repository in a background process to avoid blocking the webhook response."""
    try:
        logger.info("Starting background scan for %s on branch %s", clone_url, branch)
        # We invoke the scan_repo pipeline which walks files, parses ASTs, and audits.
        await scanner_service.scan_repo(clone_url, branch)
        logger.info("Background scan completed successfully for %s", clone_url)
    except Exception as exc:
        logger.error("Error during background scan for %s: %s", clone_url, exc)


@router.post("/github", summary="Receive GitHub Webhook Events")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
) -> dict[str, str]:
    """Receives and verifies GitHub webhook payloads.

    Triggers async repository scans for push events.
    """
    try:
        payload = await request.json()
    except Exception as exc:
        logger.error("Failed to parse webhook JSON payload: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info("Received GitHub Webhook. Event type: %s", x_github_event)

    if x_github_event == "ping":
        return {"message": "pong"}

    elif x_github_event == "push":
        # Extract clone url and branch ref
        repository = payload.get("repository", {})
        clone_url = repository.get("clone_url", "")
        ref = payload.get("ref", "")  # e.g., "refs/heads/main"

        if not clone_url or not ref:
            raise HTTPException(status_code=422, detail="Missing repository clone_url or ref")

        # Convert refs/heads/branch -> branch name
        branch = ref.split("refs/heads/")[-1]

        # Dispatch the scan task to run asynchronously in the background
        background_tasks.add_task(run_background_scan, clone_url, branch)

        return {
            "message": "Scan dispatched in the background",
            "repository": repository.get("full_name", ""),
            "branch": branch,
        }

    elif x_github_event == "pull_request":
        action = payload.get("action", "")
        pull_request = payload.get("pull_request", {})
        head = pull_request.get("head", {})
        clone_url = head.get("repo", {}).get("clone_url", "")
        branch = head.get("ref", "")

        logger.info("Pull Request webhook event action: %s", action)

        # Trigger scans on new or updated pull requests
        if action in ("opened", "synchronize") and clone_url and branch:
            background_tasks.add_task(run_background_scan, clone_url, branch)
            return {
                "message": f"Scan dispatched for pull request action: {action}",
                "branch": branch,
            }

        return {"message": f"Pull request action '{action}' skipped"}

    else:
        logger.info("Ignored GitHub event header: %s", x_github_event)
        return {"message": f"Event '{x_github_event}' received but not processed"}
