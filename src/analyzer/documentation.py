"""
RepoDoctor AI - Documentation Analyzer
Evaluates README structure, docstring coverage, usage instructions, and licensing.
"""

from __future__ import annotations
import ast
from typing import List, Tuple
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher, RepoFile


class DocumentationAnalyzer:
    """Analyzes README clarity, API docstring coverage, and project documentation hygiene."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        issues.extend(self._check_readme())
        issues.extend(self._check_docstrings())
        issues.extend(self._check_license())
        return issues

    def _check_readme(self) -> List[Issue]:
        issues = []
        readme_file = self.fetcher.get_file("README.md") or self.fetcher.get_file("readme.md")
        if not readme_file:
            issues.append(
                Issue(
                    id="DOC-NOREADME",
                    category=Category.DOCUMENTATION,
                    title="Missing README.md Documentation",
                    severity=Severity.HIGH,
                    file_path="README.md",
                    line_number=1,
                    risk_explanation="Repository has no README file. Users, collaborators, and recruiters cannot understand the project objective, installation procedure, or execution commands.",
                    recommendation="Add a comprehensive README.md including overview, installation guide, architecture diagram, and quickstart examples.",
                    confidence=0.99,
                    auto_fixable=True
                )
            )
            return issues

        content = readme_file.content.lower()
        if len(readme_file.content.strip()) < 150:
            issues.append(
                Issue(
                    id="DOC-SPARSE-README",
                    category=Category.DOCUMENTATION,
                    title="Sparse / Incomplete README.md",
                    severity=Severity.MEDIUM,
                    file_path="README.md",
                    line_number=1,
                    code_snippet=readme_file.content[:100],
                    risk_explanation="README contains less than 150 characters of description, lacking adequate installation instructions, architecture overview, and usage examples.",
                    recommendation="Enrich README with project badges, architecture overview, quickstart, and testing commands.",
                    confidence=0.95,
                    auto_fixable=True
                )
            )

        # Check essential sections
        essential_sections = ["install", "usage", "example"]
        missing_sections = [s for s in essential_sections if s not in content]
        if missing_sections:
            issues.append(
                Issue(
                    id="DOC-SECTIONS",
                    category=Category.DOCUMENTATION,
                    title=f"README Missing Essential Sections ({', '.join(missing_sections)})",
                    severity=Severity.LOW,
                    file_path="README.md",
                    line_number=1,
                    risk_explanation=f"README does not contain standard sections for {', '.join(missing_sections)}, increasing user friction during onboarding.",
                    recommendation="Add explicit '## Installation' and '## Usage' sections with copy-pasteable command snippets.",
                    confidence=0.90,
                    auto_fixable=True
                )
            )

        return issues

    def _check_docstrings(self) -> List[Issue]:
        issues = []
        py_files = [f for f in self.fetcher.get_python_files() if not f.relative_path.startswith("tests/")]
        if not py_files:
            return issues

        total_defs = 0
        documented_defs = 0

        for pf in py_files:
            if not pf.ast_tree:
                continue
            for node in ast.walk(pf.ast_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not node.name.startswith("_"):
                        total_defs += 1
                        if ast.get_docstring(node):
                            documented_defs += 1

        if total_defs > 4:
            ratio = documented_defs / total_defs
            if ratio < 0.40:
                issues.append(
                    Issue(
                        id="DOC-LOWDOCSTRINGS",
                        category=Category.DOCUMENTATION,
                        title=f"Low Public API Docstring Coverage ({ratio:.1%})",
                        severity=Severity.MEDIUM if ratio < 0.20 else Severity.LOW,
                        file_path=py_files[0].relative_path,
                        line_number=1,
                        risk_explanation=f"Only {documented_defs} of {total_defs} ({ratio:.1%}) public functions/classes have docstrings. Lack of documentation hampers code understanding and API usage.",
                        recommendation="Add standard Google or NumPy style docstrings explaining inputs, outputs, exceptions, and side-effects.",
                        confidence=0.93,
                        auto_fixable=False
                    )
                )

        return issues

    def _check_license(self) -> List[Issue]:
        issues = []
        license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "UNLICENSE"]
        has_license = any(self.fetcher.get_file(lf) is not None for lf in license_files)
        if not has_license:
            issues.append(
                Issue(
                    id="DOC-NOLICENSE",
                    category=Category.DOCUMENTATION,
                    title="Missing Open-Source LICENSE File",
                    severity=Severity.LOW,
                    file_path="LICENSE",
                    line_number=1,
                    risk_explanation="Repository does not specify an open-source license. By default, all rights are reserved and third parties cannot legally use or contribute to the project.",
                    recommendation="Add an MIT, Apache 2.0, or BSD 3-Clause LICENSE file.",
                    confidence=0.98,
                    auto_fixable=True
                )
            )
        return issues
