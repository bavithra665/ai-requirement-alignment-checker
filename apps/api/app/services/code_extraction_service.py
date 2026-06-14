"""
Code Extraction Service
Phase 1: Python AST-based extraction of functions, classes, and API endpoints.
Phase 2 placeholder: Tree-sitter for JavaScript/TypeScript (not yet implemented).

Produces normalized CodeArtifact records stored in PostgreSQL.
"""
from __future__ import annotations

import ast
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_artifact import ArtifactType
from app.schemas.code_artifact import CodeArtifactCreate
from app.repositories.code_artifact_repository import code_artifact_repo

logger = logging.getLogger(__name__)

# Known FastAPI / Flask / Django REST framework route decorators
_FASTAPI_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
_FLASK_DECORATORS = {"route", "get", "post", "put", "patch", "delete"}
_DJANGO_PATTERNS = {"path", "re_path", "url"}


class CodeExtractionService:

    # ──────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────

    def extract_from_python(self, source: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse Python source with the built-in `ast` module.
        Returns a list of symbol dicts: {type, name, metadata}.
        """
        results: List[Dict[str, Any]] = []
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            logger.warning(f"AST parse error in {file_path}: {exc}")
            return results

        for node in ast.walk(tree):
            # ── Functions & methods ───────────────────────────────────────
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = self._get_decorator_names(node)
                args = [a.arg for a in node.args.args]

                # Detect FastAPI/Flask/Django REST endpoint decorators
                endpoint_info = self._detect_python_endpoint(node, decorators)
                if endpoint_info:
                    results.append({
                        "artifact_type": ArtifactType.API_ENDPOINT,
                        "artifact_name": endpoint_info["path"],
                        "metadata": {
                            "http_method": endpoint_info["method"],
                            "function_name": node.name,
                            "line_number": node.lineno,
                            "decorators": decorators,
                        },
                    })

                # Always record the function itself
                results.append({
                    "artifact_type": ArtifactType.FUNCTION,
                    "artifact_name": node.name,
                    "metadata": {
                        "line_number": node.lineno,
                        "args": args,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": decorators,
                    },
                })

            # ── Classes ───────────────────────────────────────────────────
            elif isinstance(node, ast.ClassDef):
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(f"{base.attr}")

                results.append({
                    "artifact_type": ArtifactType.CLASS,
                    "artifact_name": node.name,
                    "metadata": {
                        "line_number": node.lineno,
                        "base_classes": base_names,
                    },
                })

        return results

    def extract_from_javascript(self, source: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Phase 2: Tree-sitter-based extraction for JS/TS.
        Currently returns empty list — placeholder for future implementation.
        """
        logger.info(f"JS/TS extraction not yet implemented for {file_path} (Phase 2 — Tree-sitter)")
        return []

    def extract_symbols(self, source: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Route to the correct extractor based on file extension.
        """
        fp = file_path.lower()
        if fp.endswith(".py"):
            return self.extract_from_python(source, file_path)
        elif fp.endswith((".js", ".ts", ".jsx", ".tsx")):
            return self.extract_from_javascript(source, file_path)
        return []

    async def process_pr_files(
        self,
        db: AsyncSession,
        *,
        pull_request_id: UUID,
        repository_url: str,
        changed_files: List[str],
        head_sha: Optional[str],
        current_user_id: UUID,
    ) -> Dict[str, Any]:
        """
        For each changed file in a PR, fetch content from GitHub (if available)
        and run symbol extraction, writing normalized CodeArtifact rows.
        Existing artifacts for this PR are deleted first (idempotent re-run).
        """
        # Avoid circular import — import here
        from app.services.github_service import github_service

        # Clear previous extraction results for this PR
        await code_artifact_repo.delete_by_pull_request(db=db, pull_request_id=pull_request_id)

        total_functions = 0
        total_classes = 0
        total_endpoints = 0
        processed_files = 0

        for file_path in changed_files:
            # Only extract from supported source file types
            if not file_path.lower().endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                continue

            # Fetch file content from GitHub
            content = await github_service.get_file_content(
                repository_url=repository_url,
                file_path=file_path,
                ref=head_sha or "main",
            )
            if content is None:
                logger.info(f"Skipping {file_path}: could not fetch content")
                continue

            symbols = self.extract_symbols(content, file_path)
            processed_files += 1

            for sym in symbols:
                artifact_in = CodeArtifactCreate(
                    pull_request_id=pull_request_id,
                    artifact_type=sym["artifact_type"],
                    artifact_name=sym["artifact_name"],
                    file_path=file_path,
                    artifact_metadata=sym.get("metadata"),
                )
                await code_artifact_repo.create(
                    db=db, obj_in=artifact_in, created_by_id=current_user_id
                )

                if sym["artifact_type"] == ArtifactType.FUNCTION:
                    total_functions += 1
                elif sym["artifact_type"] == ArtifactType.CLASS:
                    total_classes += 1
                elif sym["artifact_type"] == ArtifactType.API_ENDPOINT:
                    total_endpoints += 1

        return {
            "processed_files": processed_files,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_endpoints": total_endpoints,
        }

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _get_decorator_names(self, node: ast.FunctionDef) -> List[str]:
        names = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    names.append(dec.func.attr)
                elif isinstance(dec.func, ast.Name):
                    names.append(dec.func.id)
        return names

    def _detect_python_endpoint(
        self, node: ast.FunctionDef, decorators: List[str]
    ) -> Optional[Dict[str, str]]:
        """
        Inspect decorators to find HTTP route definitions.
        Supports FastAPI (router.get, app.post), Flask (@app.route), Django (path).
        Returns {path, method} or None.
        """
        for dec in node.decorator_list:
            # FastAPI / Flask style: @router.get("/path") or @app.post("/path")
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                method = dec.func.attr.lower()
                if method in _FASTAPI_METHODS or method in _FLASK_DECORATORS:
                    path = self._extract_first_string_arg(dec)
                    return {"path": path or f"/{node.name}", "method": method.upper()}

            # Django: path("url/", view)  — less reliable, skip for now
        return None

    def _extract_first_string_arg(self, call_node: ast.Call) -> Optional[str]:
        if call_node.args:
            first = call_node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                return first.value
        return None


code_extraction_service = CodeExtractionService()
