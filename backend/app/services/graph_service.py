"""
Plexus Backend — Graph Service

Manages the construction and query of code syntax graphs in Neo4j.
Maps files, classes, functions, and import modules as nodes, and draws
ownership, inheritance, call, and dependency relationships between them.
"""

from __future__ import annotations

import logging
import re
from uuid import UUID

from app.core.database import db_manager

logger = logging.getLogger(__name__)


class GraphService:
    """Service to write and query code AST dependency graphs in Neo4j."""

    @property
    def is_connected(self) -> bool:
        """Helper to determine if the Neo4j backend is connected and online."""
        return db_manager.neo4j_driver is not None

    # ------------------------------------------------------------------
    # Clear Graph
    # ------------------------------------------------------------------

    def clear_file_graph(self, repo_id: UUID, file_path: str) -> None:
        """Removes all File, Class, and Function nodes matching a specific path.

        Ensures old AST representations are purged before a rescan.

        Args:
            repo_id: Repository UUID.
            file_path: Relative file path.
        """
        if not self.is_connected:
            logger.info("Neo4j offline. Skipping clear_file_graph for %s", file_path)
            return

        query = """
        MATCH (f:File {repo_id: $repo_id, path: $file_path})
        OPTIONAL MATCH (f)-[:CONTAINS]->(c:Class)
        OPTIONAL MATCH (f)-[:CONTAINS]->(func:Function)
        DETACH DELETE f, c, func
        """
        params = {"repo_id": str(repo_id), "file_path": file_path}

        try:
            with db_manager.get_neo4j_session() as session:
                session.run(query, params)
            logger.info("Cleared Neo4j graph for file: %s", file_path)
        except Exception as exc:
            logger.error("Failed to clear Neo4j graph for %s: %s", file_path, exc)

    # ------------------------------------------------------------------
    # Upsert Graph
    # ------------------------------------------------------------------

    def upsert_file_graph(
        self,
        repo_id: UUID,
        file_path: str,
        ast_data: dict,
    ) -> None:
        """Constructs class, function, call, and import nodes/edges in Neo4j.

        Args:
            repo_id: Repository UUID.
            file_path: Relative path of the parsed file.
            ast_data: Extracted tree-sitter AST data.
        """
        if not self.is_connected:
            logger.info("Neo4j offline. Skipping upsert_file_graph for %s", file_path)
            return

        # 1. Clear any old data
        self.clear_file_graph(repo_id, file_path)

        repo_id_str = str(repo_id)

        try:
            with db_manager.get_neo4j_session() as session:
                # 2. Merge File Node
                session.run(
                    """
                    MERGE (f:File {repo_id: $repo_id, path: $file_path})
                    SET f.updated_at = timestamp()
                    """,
                    {"repo_id": repo_id_str, "file_path": file_path},
                )

                # 3. Create Import / Module Nodes
                for imp in ast_data.get("imports", []):
                    text = imp.get("text", "")
                    # Extract a clean module name (e.g. "from os import path" -> "os")
                    module_name = self._clean_module_name(text)
                    if module_name:
                        session.run(
                            """
                            MATCH (f:File {repo_id: $repo_id, path: $file_path})
                            MERGE (m:Module {name: $module_name})
                            MERGE (f)-[:DEPENDS_ON]->(m)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "module_name": module_name,
                            },
                        )

                # 4. Create Class Nodes
                for cls in ast_data.get("classes", []):
                    class_name = cls.get("name", "AnonymousClass")
                    bases = cls.get("bases", [])
                    session.run(
                        """
                        MATCH (f:File {repo_id: $repo_id, path: $file_path})
                        MERGE (c:Class {name: $class_name, repo_id: $repo_id, path: $file_path})
                        MERGE (f)-[:CONTAINS]->(c)
                        """,
                        {
                            "repo_id": repo_id_str,
                            "file_path": file_path,
                            "class_name": class_name,
                        },
                    )
                    # inheritance relationships
                    for base in bases:
                        session.run(
                            """
                            MATCH (c:Class {name: $class_name, repo_id: $repo_id, path: $file_path})
                            MERGE (p:Class {name: $parent_name})
                            MERGE (c)-[:INHERITS_FROM]->(p)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "class_name": class_name,
                                "parent_name": base,
                            },
                        )

                # 5. Create Function Nodes & link to Class/File
                for func in ast_data.get("functions", []):
                    func_name = func.get("name", "anonymous")
                    line_start = func.get("line_start", 1)
                    line_end = func.get("line_end", 1)

                    # Determine if it's a method by checking if line ranges fall inside a Class
                    parent_class = None
                    for cls in ast_data.get("classes", []):
                        if (
                            cls.get("line_start", 0) <= line_start
                            and line_end <= cls.get("line_end", 0)
                        ):
                            parent_class = cls.get("name")
                            break

                    if parent_class:
                        session.run(
                            """
                            MATCH (c:Class {name: $class_name, repo_id: $repo_id, path: $file_path})
                            MERGE (fn:Function {name: $func_name, repo_id: $repo_id, path: $file_path})
                            SET fn.line_start = $line_start, fn.line_end = $line_end
                            MERGE (c)-[:DEFINES]->(fn)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "class_name": parent_class,
                                "func_name": func_name,
                                "line_start": line_start,
                                "line_end": line_end,
                            },
                        )
                    else:
                        session.run(
                            """
                            MATCH (f:File {repo_id: $repo_id, path: $file_path})
                            MERGE (fn:Function {name: $func_name, repo_id: $repo_id, path: $file_path})
                            SET fn.line_start = $line_start, fn.line_end = $line_end
                            MERGE (f)-[:CONTAINS]->(fn)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "func_name": func_name,
                                "line_start": line_start,
                                "line_end": line_end,
                            },
                        )

                # 6. Create Calls Relationships (Link Function -> Function)
                for call in ast_data.get("calls", []):
                    call_name = call.get("function_name", "unknown")
                    call_line = call.get("line", 1)
                    
                    # Split method chain to get base function name (e.g. "db.query" -> "query")
                    called_func_name = call_name.split(".")[-1]

                    # Find which function node contains this call
                    caller_func = None
                    for func in ast_data.get("functions", []):
                        if func.get("line_start", 0) <= call_line <= func.get("line_end", 0):
                            caller_func = func.get("name")
                            break

                    if caller_func:
                        # Call is inside a Function node
                        session.run(
                            """
                            MATCH (caller:Function {name: $caller_name, repo_id: $repo_id, path: $file_path})
                            MERGE (callee:Function {name: $callee_name})
                            MERGE (caller)-[:CALLS]->(callee)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "caller_name": caller_func,
                                "callee_name": called_func_name,
                            },
                        )
                    else:
                        # Call is at the module file-level
                        session.run(
                            """
                            MATCH (f:File {repo_id: $repo_id, path: $file_path})
                            MERGE (callee:Function {name: $callee_name})
                            MERGE (f)-[:CALLS]->(callee)
                            """,
                            {
                                "repo_id": repo_id_str,
                                "file_path": file_path,
                                "callee_name": called_func_name,
                            },
                        )

            logger.info("Successfully pushed AST graph to Neo4j for: %s", file_path)
        except Exception as exc:
            logger.error("Failed to build Neo4j graph for %s: %s", file_path, exc)

    # ------------------------------------------------------------------
    # Helper to clean module names
    # ------------------------------------------------------------------

    def _clean_module_name(self, import_text: str) -> str | None:
        """Parses import lines and extracts the core module dependency.

        Examples:
            "import os" -> "os"
            "from sqlalchemy import select" -> "sqlalchemy"
            "const db = require('db-connector')" -> "db-connector"
        """
        text = import_text.strip()
        
        # 1. require('module')
        if "require(" in text:
            m = re.search(r"require\(['\"]([^'\"]+)['\"]\)", text)
            if m:
                return m.group(1)
        
        # 2. ES6: import ... from 'module'
        if text.startswith("import") and "from" in text:
            m = re.search(r"from\s+['\"]([^'\"]+)['\"]", text)
            if m:
                return m.group(1)
            
        # 3. Python: from module import ...
        if text.startswith("from"):
            parts = text.split()
            if len(parts) > 1:
                return parts[1].split(".")[0]
            
        # 4. Python: import module
        if text.startswith("import"):
            parts = text.split()
            if len(parts) > 1:
                # Remove aliases or sub-packages (e.g. "import os.path" -> "os")
                return parts[1].split(".")[0].split(",")[0]

        return None
