#!/usr/bin/env python3
"""
Plexus Backend — Graph Router

Exposes the Neo4j code property graph for interactive exploration
and blast-radius analysis.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.error_handler import NotFoundException
from app.services.graph_service import GraphService
from app.models.scan import Scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get(
    "/blast-radius/{scan_id}",
    summary="Get blast radius subgraph for a scan",
)
def get_blast_radius(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve the code dependency graph for a given scan's repository.

    Returns nodes (files, functions, classes, vulnerabilities) and edges
    (imports, calls, contains, affects) for interactive visualisation.
    """
    scan = db.get(Scan, scan_id)
    if not scan:
        raise NotFoundException(f"Scan {scan_id} not found")

    repo_id = scan.repository_id
    graph_svc = GraphService()

    if not graph_svc.is_connected:
        # Return mock data if Neo4j is offline
        return {
            "nodes": [
                {"id": "n1", "name": "main.py", "type": "file"},
                {"id": "n2", "name": "config.py", "type": "file"},
                {"id": "n3", "name": "security.py", "type": "file"},
                {"id": "n4", "name": "get_user()", "type": "function"},
                {"id": "n5", "name": "hash_password()", "type": "function"},
                {"id": "n6", "name": "UserRouter", "type": "class"},
                {"id": "n7", "name": "/api/v1/auth/login", "type": "api"},
                {"id": "v1", "name": "SQL Injection", "type": "vulnerability"},
            ],
            "links": [
                {"source": "n1", "target": "n2", "type": "IMPORTS"},
                {"source": "n1", "target": "n3", "type": "IMPORTS"},
                {"source": "n7", "target": "n4", "type": "CALLS"},
                {"source": "n4", "target": "n5", "type": "CALLS"},
                {"source": "n4", "target": "n6", "type": "CONTAINS"},
                {"source": "v1", "target": "n4", "type": "AFFECTS"},
            ],
        }

    try:
        # Fetch all nodes and relationships for this repository
        query = """
        MATCH (a)-[r]->(b)
        WHERE a.repo_id = $repo_id OR b.repo_id = $repo_id
        RETURN {
            source: {id: a.id, name: a.name, type: labels(a)[0]},
            target: {id: b.id, name: b.name, type: labels(b)[0]},
            rel_type: type(r)
        } as edge
        LIMIT 200
        """
        with graph_svc.driver.session() as session:
            result = session.run(query, {"repo_id": str(repo_id)})
            edges = [record["edge"] for record in result]

        # Build unique nodes list
        nodes_map = {}
        for edge in edges:
            for key in ("source", "target"):
                node = edge[key]
                nid = node.get("id") or node.get("name")
                if nid and nid not in nodes_map:
                    nodes_map[nid] = {
                        "id": nid,
                        "name": node.get("name", "Unknown"),
                        "type": node.get("type", "Unknown"),
                    }

        links = [
            {"source": edge["source"].get("id") or edge["source"].get("name"),
             "target": edge["target"].get("id") or edge["target"].get("name"),
             "type": edge["rel_type"]}
            for edge in edges
        ]

        return {"nodes": list(nodes_map.values()), "links": links}

    except Exception as exc:
        logger.error("Failed to query graph for blast radius: %s", exc)
        raise NotFoundException(f"Graph data unavailable for scan {scan_id}")


@router.get(
    "/context/{repo_id}",
    summary="Get multi-hop file context from graph",
)
def get_file_context(
    repo_id: UUID,
    file_path: str,
    hop_depth: int = 2,
):
    """Fetch multi-hop dependency context for a specific file."""
    graph_svc = GraphService()
    if not graph_svc.is_connected:
        return {"context": []}

    try:
        context = graph_svc.get_file_context(repo_id, file_path, hop_depth)
        return {"context": context}
    except Exception as exc:
        logger.error("Failed to get file context: %s", exc)
        return {"context": []}
