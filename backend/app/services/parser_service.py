"""
Plexus Backend — Parser Service

Integrates Tree-sitter for AST-based code analysis, extracting imports,
classes, functions, calls, and variables from Python and JavaScript.
"""

from __future__ import annotations

import logging
from typing import Any

from tree_sitter import Language, Node, Parser
import tree_sitter_javascript
import tree_sitter_python

logger = logging.getLogger(__name__)


class ParserService:
    """Service to parse Python and JS/TS source code and extract AST entities."""

    def __init__(self) -> None:
        # Load language specifications
        try:
            self._py_lang = Language(tree_sitter_python.language())
            self._js_lang = Language(tree_sitter_javascript.language())
            
            # Setup parsers
            self._py_parser = Parser(self._py_lang)
            self._js_parser = Parser(self._js_lang)
            logger.info("Tree-sitter languages loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load Tree-sitter languages: %s", exc)
            raise exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_code(self, code: str | bytes, language: str) -> dict[str, list[dict[str, Any]]]:
        """Parses source code and extracts high-level semantic entities.

        Args:
            code: Source code content as a string or bytes.
            language: Target programming language ('python', 'javascript', etc.).

        Returns:
            A dictionary of extracted entities categorized by type:
            {
                "imports": [...],
                "classes": [...],
                "functions": [...],
                "calls": [...],
                "assignments": [...]
            }
        """
        if isinstance(code, str):
            code_bytes = code.encode("utf-8")
        else:
            code_bytes = code

        lang_lower = language.lower()
        if lang_lower in ("python", "py"):
            parser = self._py_parser
        elif lang_lower in ("javascript", "js", "typescript", "ts", "jsx", "tsx"):
            parser = self._js_parser
        else:
            # Unsupported language, return empty mapping
            logger.warning("Unsupported language for parsing: %s", language)
            return {
                "imports": [],
                "classes": [],
                "functions": [],
                "calls": [],
                "assignments": [],
            }

        try:
            tree = parser.parse(code_bytes)
            entities = {
                "imports": [],
                "classes": [],
                "functions": [],
                "calls": [],
                "assignments": [],
            }
            self._traverse_node(tree.root_node, code_bytes, lang_lower, entities)
            return entities
        except Exception as exc:
            logger.error("Error parsing code with tree-sitter: %s", exc)
            return {
                "imports": [],
                "classes": [],
                "functions": [],
                "calls": [],
                "assignments": [],
            }

    # ------------------------------------------------------------------
    # AST Traversal (Recursive walker)
    # ------------------------------------------------------------------

    def _traverse_node(
        self,
        node: Node,
        code_bytes: bytes,
        lang: str,
        entities: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Recursively walks AST nodes and aggregates target structures."""
        node_type = node.type
        start_line = node.start_point[0] + 1  # 0-indexed to 1-indexed
        end_line = node.end_point[0] + 1

        # Helper to decode node text
        def get_text(n: Node) -> str:
            return n.text.decode("utf-8", errors="ignore")

        # --- PYTHON AST MAPPINGS ---
        if lang in ("python", "py"):
            # Imports
            if node_type in ("import_statement", "import_from_statement"):
                entities["imports"].append({
                    "type": node_type,
                    "text": get_text(node),
                    "line_start": start_line,
                    "line_end": end_line,
                })

            # Classes
            elif node_type == "class_definition":
                name_node = node.child_by_field_name("name")
                bases = []
                superclasses = node.child_by_field_name("superclasses")
                if superclasses:
                    # superclasses is an argument_list of bases
                    for child in superclasses.children:
                        if child.type in ("identifier", "attribute"):
                            bases.append(get_text(child))

                entities["classes"].append({
                    "name": get_text(name_node) if name_node else "AnonymousClass",
                    "bases": bases,
                    "line_start": start_line,
                    "line_end": end_line,
                })

            # Functions/Methods
            elif node_type == "function_definition":
                name_node = node.child_by_field_name("name")
                params = []
                param_list = node.child_by_field_name("parameters")
                if param_list:
                    for child in param_list.children:
                        if child.type in ("identifier", "dictionary_splat_pattern", "list_splat_pattern", "typed_parameter", "default_parameter"):
                            params.append(get_text(child))

                entities["functions"].append({
                    "name": get_text(name_node) if name_node else "anonymous_func",
                    "parameters": params,
                    "line_start": start_line,
                    "line_end": end_line,
                })

            # Method/Function Calls
            elif node_type == "call":
                func_node = node.child_by_field_name("function")
                entities["calls"].append({
                    "function_name": get_text(func_node) if func_node else "unknown_call",
                    "line": start_line,
                    "text": get_text(node),
                })

            # Variable Assignments
            elif node_type == "assignment":
                left_nodes = node.child_by_field_name("left")
                right_node = node.child_by_field_name("right")
                if left_nodes and right_node:
                    entities["assignments"].append({
                        "variable": get_text(left_nodes),
                        "value": get_text(right_node),
                        "line": start_line,
                    })

        # --- JAVASCRIPT AST MAPPINGS ---
        else:
            # Imports
            if node_type in ("import_statement", "export_statement"):
                entities["imports"].append({
                    "type": node_type,
                    "text": get_text(node),
                    "line_start": start_line,
                    "line_end": end_line,
                })
            elif node_type == "call_expression":
                # Check for require('module')
                function_node = node.child_by_field_name("function") or node.child(0)
                if function_node and get_text(function_node) == "require":
                    entities["imports"].append({
                        "type": "require_call",
                        "text": get_text(node),
                        "line_start": start_line,
                        "line_end": end_line,
                    })
                else:
                    # Regular call expression
                    callee = get_text(function_node) if function_node else "unknown_call"
                    entities["calls"].append({
                        "function_name": callee,
                        "line": start_line,
                        "text": get_text(node),
                    })

            # Classes
            elif node_type in ("class_declaration", "class_expression"):
                name_node = node.child_by_field_name("name")
                heritage = node.child_by_field_name("heritage")
                bases = []
                if heritage:
                    # extends keyword and parent classes
                    bases.append(get_text(heritage))

                entities["classes"].append({
                    "name": get_text(name_node) if name_node else "AnonymousClass",
                    "bases": bases,
                    "line_start": start_line,
                    "line_end": end_line,
                })

            # Functions / Methods
            elif node_type in ("function_declaration", "method_definition", "arrow_function"):
                name_node = node.child_by_field_name("name")
                # Methods may have names stored differently
                if not name_node and node_type == "method_definition":
                    # First identifier child is name
                    for child in node.children:
                        if child.type in ("property_identifier", "identifier"):
                            name_node = child
                            break

                params = []
                param_list = node.child_by_field_name("parameters")
                if param_list:
                    for child in param_list.children:
                        if child.type in ("identifier", "formal_parameter", "assignment_pattern", "rest_parameter"):
                            params.append(get_text(child))

                # Extract variable-assigned functions (e.g. const foo = () => {})
                func_name = get_text(name_node) if name_node else "anonymous"
                if node_type == "arrow_function":
                    # Check parent declaration to see if assigned to a variable name
                    parent = node.parent
                    if parent and parent.type == "variable_declarator":
                        id_node = parent.child_by_field_name("name")
                        if id_node:
                            func_name = get_text(id_node)

                entities["functions"].append({
                    "name": func_name,
                    "parameters": params,
                    "line_start": start_line,
                    "line_end": end_line,
                })

            # Variable Assignments
            elif node_type == "variable_declarator":
                id_node = node.child_by_field_name("name")
                val_node = node.child_by_field_name("value")
                if id_node and val_node:
                    entities["assignments"].append({
                        "variable": get_text(id_node),
                        "value": get_text(val_node),
                        "line": start_line,
                    })

        # Recurse children
        for child in node.children:
            self._traverse_node(child, code_bytes, lang, entities)
