"""
RepoDoctor AI - Architecture Analyzer
Evaluates project structure, modularity, circular dependencies, god files, and layout.
"""

from __future__ import annotations
import ast
import os
from typing import List, Dict, Set
from pathlib import Path
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher, RepoFile


class ArchitectureAnalyzer:
    """Analyzes repository layout, modularity, God files, and module coupling."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        issues.extend(self._check_project_layout())
        issues.extend(self._check_god_files())
        issues.extend(self._check_circular_imports())
        issues.extend(self._check_package_init())
        return issues

    def _check_project_layout(self) -> List[Issue]:
        issues = []
        py_files = self.fetcher.get_python_files()
        if not py_files:
            return issues

        # Check if all python files are dumped in root directory without subpackages
        root_py = [f for f in py_files if "/" not in f.relative_path and "\\" not in f.relative_path]
        if len(root_py) > 6 and len(py_files) == len(root_py):
            issues.append(
                Issue(
                    id="ARCH-001",
                    category=Category.ARCHITECTURE,
                    title="Flat Unstructured Root Directory",
                    severity=Severity.MEDIUM,
                    file_path=root_py[0].relative_path,
                    risk_explanation="All source files reside in the root folder without package modularity (e.g. src/ or package namespace). This causes namespace pollution and hinders maintainability as the project scales.",
                    recommendation="Adopt a standard 'src/' or modular package directory structure with cohesive subpackages.",
                    confidence=0.90,
                    auto_fixable=False
                )
            )
        return issues

    def _check_god_files(self) -> List[Issue]:
        issues = []
        for pf in self.fetcher.get_python_files():
            # God file threshold: > 600 lines with high function/class count
            if pf.loc > 600:
                issues.append(
                    Issue(
                        id=f"ARCH-GOD-{abs(hash(pf.relative_path)) % 10000}",
                        category=Category.ARCHITECTURE,
                        title=f"Monolithic 'God File' Detected ({pf.loc} LOC)",
                        severity=Severity.HIGH if pf.loc > 1000 else Severity.MEDIUM,
                        file_path=pf.relative_path,
                        line_number=1,
                        end_line_number=min(pf.loc, 50),
                        code_snippet=f"# File: {pf.relative_path} ({pf.loc} lines)",
                        risk_explanation=f"File '{pf.relative_path}' contains {pf.loc} lines of code. High cyclomatic mass violates Single Responsibility Principle (SRP), making unit testing and maintenance difficult.",
                        recommendation="Refactor and decouple this monolithic module into specialized submodules (e.g., separating core domain logic, utilities, and I/O).",
                        confidence=0.95,
                        auto_fixable=False
                    )
                )
        return issues

    def _check_package_init(self) -> List[Issue]:
        issues = []
        dirs_with_py: Set[str] = set()
        for pf in self.fetcher.get_python_files():
            parent_dir = os.path.dirname(pf.relative_path)
            if parent_dir and parent_dir != "tests":
                dirs_with_py.add(parent_dir)

        for d in dirs_with_py:
            init_file = f"{d}/__init__.py"
            if not self.fetcher.get_file(init_file):
                issues.append(
                    Issue(
                        id=f"ARCH-INIT-{abs(hash(d)) % 10000}",
                        category=Category.ARCHITECTURE,
                        title=f"Missing __init__.py in package directory '{d}'",
                        severity=Severity.LOW,
                        file_path=f"{d}/__init__.py",
                        line_number=1,
                        code_snippet="",
                        risk_explanation="Python package directory lacks an __init__.py marker, which may cause import resolution failures across different Python runtime environments.",
                        recommendation=f"Add an __init__.py file in '{d}' to clearly define it as a Python package.",
                        confidence=0.98,
                        auto_fixable=True
                    )
                )
        return issues

    def _check_circular_imports(self) -> List[Issue]:
        issues = []
        # Build basic dependency graph from AST imports
        import_graph: Dict[str, Set[str]] = {}
        py_files = self.fetcher.get_python_files()
        file_modules = {Path(f.relative_path).stem: f.relative_path for f in py_files}

        for pf in py_files:
            if not pf.ast_tree:
                continue
            src_stem = Path(pf.relative_path).stem
            import_graph[src_stem] = set()

            for node in ast.walk(pf.ast_tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name.split(".")[0]
                        if target in file_modules and target != src_stem:
                            import_graph[src_stem].add(target)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        target = node.module.split(".")[0]
                        if target in file_modules and target != src_stem:
                            import_graph[src_stem].add(target)

        # Detect direct circular imports: A -> B and B -> A
        detected_pairs = set()
        for mod_a, deps in import_graph.items():
            for mod_b in deps:
                if mod_a in import_graph.get(mod_b, set()):
                    pair_key = tuple(sorted([mod_a, mod_b]))
                    if pair_key not in detected_pairs:
                        detected_pairs.add(pair_key)
                        file_a = file_modules.get(mod_a, mod_a)
                        file_b = file_modules.get(mod_b, mod_b)
                        issues.append(
                            Issue(
                                id=f"ARCH-CIRC-{abs(hash(pair_key)) % 10000}",
                                category=Category.ARCHITECTURE,
                                title=f"Circular Import Dependency: {mod_a} <-> {mod_b}",
                                severity=Severity.HIGH,
                                file_path=file_a,
                                line_number=1,
                                risk_explanation=f"Direct circular dependency detected between '{file_a}' and '{file_b}'. Circular imports cause partially initialized module errors at runtime.",
                                recommendation="Extract shared dependencies into a common base interface module or use lazy imports.",
                                confidence=0.92,
                                auto_fixable=False
                            )
                        )
        return issues
