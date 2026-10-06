"""
RepoDoctor AI - Patch Security Gate 🛡️
Strict multi-tier security boundary that validates candidate LLM and heuristic patches before execution.
Ensures no malicious code, unwanted imports, path traversals, or oversized hallucinations are applied.
"""

from __future__ import annotations

import ast
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.models import Patch


class SecurityGateDecision(BaseModel):
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    blocked_imports: list[str] = Field(default_factory=list)
    ast_vulnerabilities: list[str] = Field(default_factory=list)
    diff_line_change: int = 0


class PatchSecurityGate:
    """Multi-tiered security gate for patch verification."""

    # Disallowed dangerous modules / calls for automated patches
    FORBIDDEN_MODULES = {
        "socket",
        "ctypes",
        "pty",
        "subprocess",
        "telnetlib",
        "ftplib",
        "paramiko",
        "shutil",
        "tempfile_evil",
    }

    FORBIDDEN_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "getattr",
    }

    MAX_EXPANSION_RATIO = 3.5  # Reject if replacement is > 3.5x size of original
    MAX_LINES_ADDED = 250  # Hard ceiling on automated single-patch insertion

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root).resolve() if repo_root else None

    def evaluate(self, patch: Patch) -> SecurityGateDecision:
        """Run all security gates on the proposed patch."""
        reasons: list[str] = []
        blocked_imports: list[str] = []
        ast_vulns: list[str] = []

        # 1. Path Traversal & File Boundary Check
        path_str = patch.file_path
        if ".." in path_str or path_str.startswith("/") or path_str.startswith("\\"):
            reasons.append(f"Security Gate Blocked: Path traversal or absolute path detected in '{path_str}'")

        if self.repo_root:
            target_path = (self.repo_root / path_str).resolve()
            try:
                target_path.relative_to(self.repo_root)
            except ValueError:
                reasons.append(f"Security Gate Blocked: Target file '{path_str}' escapes repository root boundary.")

        # 2. Diff Size & Bloat / Hallucination Limits
        orig_lines = len(patch.original_code.splitlines()) if patch.original_code else 0
        new_lines = len(patch.replacement_code.splitlines()) if patch.replacement_code else 0
        line_delta = new_lines - orig_lines

        if orig_lines > 10 and (new_lines / max(orig_lines, 1)) > self.MAX_EXPANSION_RATIO:
            reasons.append(
                f"Security Gate Blocked: Replacement code size ({new_lines} lines) expands {new_lines/orig_lines:.1f}x beyond original ({orig_lines} lines)."
            )

        if line_delta > self.MAX_LINES_ADDED:
            reasons.append(
                f"Security Gate Blocked: Patch adds {line_delta} lines exceeding maximum single-patch threshold ({self.MAX_LINES_ADDED})."
            )

        # 3. AST Syntax & Static Security Analysis (For Python files)
        if patch.file_path.endswith(".py") and patch.replacement_code:
            try:
                ast.parse(patch.replacement_code, filename=patch.file_path)
            except SyntaxError as syn_err:
                reasons.append(f"Security Gate Blocked: Replacement code has invalid Python syntax ({syn_err}).")
                return SecurityGateDecision(
                    passed=False,
                    reasons=reasons,
                    diff_line_change=line_delta,
                )

            orig_imports, orig_calls = self._extract_security_features(patch.original_code, patch.file_path)
            new_imports, new_calls = self._extract_security_features(patch.replacement_code, patch.file_path)

            introduced_imports = (new_imports - orig_imports) & self.FORBIDDEN_MODULES
            for mod in introduced_imports:
                blocked_imports.append(mod)
                ast_vulns.append(f"Forbidden security module introduced by patch: '{mod}'")

            introduced_calls = new_calls - orig_calls
            for call in introduced_calls:
                ast_vulns.append(f"Dangerous call introduced by patch: '{call}()'")

        if ast_vulns:
            reasons.extend(ast_vulns)

        passed = len(reasons) == 0
        return SecurityGateDecision(
            passed=passed,
            reasons=reasons,
            blocked_imports=blocked_imports,
            ast_vulnerabilities=ast_vulns,
            diff_line_change=line_delta,
        )

    def _extract_security_features(self, code: str, file_path: str) -> tuple[set[str], set[str]]:
        """Extract imported modules and dangerous calls from code."""
        imports: set[str] = set()
        calls: set[str] = set()
        if not code or not file_path.endswith(".py"):
            return imports, calls

        try:
            tree = ast.parse(code, filename=file_path)
        except Exception:
            return imports, calls

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if (
                        isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "os"
                        and node.func.attr in {"system", "popen", "spawn"}
                    ):
                        calls.add(f"os.{node.func.attr}")
        return imports, calls

