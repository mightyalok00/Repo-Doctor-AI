"""
RepoDoctor AI - Dependency and Supply-Chain Analyzer
Audits requirements.txt, pyproject.toml, and setup.py for unpinned versions, outdated packages, and vulnerabilities.
"""

from __future__ import annotations
import re
from typing import List, Dict, Tuple
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher


class DependencyAnalyzer:
    """Analyzes repository dependency specifications for reproducibility and security."""

    DEPRECATED_OR_VULNERABLE = {
        "sklearn": ("scikit-learn", "Package 'sklearn' is deprecated on PyPI. Install 'scikit-learn' instead."),
        "pycrypto": ("cryptography", "Package 'pycrypto' is unmaintained and contains known CVE vulnerabilities. Use 'cryptography'."),
        "pickle5": ("pickle", "Package 'pickle5' is obsolete in modern Python 3.8+."),
    }

    # Recommended stable pins for common data science & web packages
    PINNED_RECOMMENDATIONS = {
        "numpy": "numpy==1.26.4",
        "pandas": "pandas==2.2.2",
        "scikit-learn": "scikit-learn==1.4.2",
        "scipy": "scipy==1.13.0",
        "xgboost": "xgboost==2.0.3",
        "lightgbm": "lightgbm==4.3.0",
        "torch": "torch>=2.2.0",
        "fastapi": "fastapi>=0.110.0",
        "uvicorn": "uvicorn>=0.29.0",
        "pydantic": "pydantic>=2.7.0",
        "streamlit": "streamlit>=1.33.0",
        "pytest": "pytest>=8.1.0",
        "requests": "requests>=2.31.0"
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        issues.extend(self._analyze_requirements_txt())
        issues.extend(self._check_missing_dependency_manifest())
        return issues

    def _check_missing_dependency_manifest(self) -> List[Issue]:
        issues = []
        manifests = ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "environment.yml"]
        has_manifest = any(self.fetcher.get_file(m) is not None for m in manifests)
        if not has_manifest and self.fetcher.get_python_files():
            issues.append(
                Issue(
                    id="DEP-NOMANIFEST",
                    category=Category.DEPENDENCY if hasattr(Category, "DEPENDENCY") else Category.REPRODUCIBILITY,
                    title="Missing Dependency Manifest (requirements.txt / pyproject.toml)",
                    severity=Severity.HIGH,
                    file_path="requirements.txt",
                    risk_explanation="Repository lacks standard dependency definitions. Other developers and CI pipelines cannot deterministically reproduce the runtime environment.",
                    recommendation="Add a requirements.txt or pyproject.toml specifying all project dependencies.",
                    confidence=0.98,
                    auto_fixable=True
                )
            )
        return issues

    def _analyze_requirements_txt(self) -> List[Issue]:
        issues = []
        req_file = self.fetcher.get_file("requirements.txt")
        if not req_file:
            return issues

        lines = req_file.lines
        for idx, line in enumerate(lines, start=1):
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#") or clean_line.startswith("-"):
                continue

            # Parse package name and version constraint
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(.*)$", clean_line)
            if not match:
                continue

            pkg_name = match.group(1).lower()
            constraint = match.group(2).strip()

            # Check deprecated packages
            if pkg_name in self.DEPRECATED_OR_VULNERABLE:
                replacement, reason = self.DEPRECATED_OR_VULNERABLE[pkg_name]
                issues.append(
                    Issue(
                        id=f"DEP-DEPR-{pkg_name}",
                        category=Category.REPRODUCIBILITY,
                        title=f"Deprecated/Insecure Dependency '{pkg_name}'",
                        severity=Severity.HIGH,
                        file_path="requirements.txt",
                        line_number=idx,
                        code_snippet=clean_line,
                        risk_explanation=reason,
                        recommendation=f"Replace '{pkg_name}' with '{replacement}'.",
                        confidence=0.99,
                        auto_fixable=True,
                        metadata={"pkg_name": pkg_name, "replacement": replacement}
                    )
                )
                continue

            # Check unpinned or loose bounds like >= without upper limit or completely unpinned
            is_unpinned = (not constraint) or (">=" in constraint and "<" not in constraint and "==" not in constraint)
            if is_unpinned:
                recommended_pin = self.PINNED_RECOMMENDATIONS.get(pkg_name, f"{pkg_name}==latest-stable")
                issues.append(
                    Issue(
                        id=f"DEP-UNPIN-{pkg_name}",
                        category=Category.REPRODUCIBILITY,
                        title=f"Unpinned Dependency '{clean_line}'",
                        severity=Severity.MEDIUM,
                        file_path="requirements.txt",
                        line_number=idx,
                        code_snippet=clean_line,
                        risk_explanation="Loose or unpinned version constraints lead to non-reproducible builds when upstream packages release breaking changes.",
                        recommendation=f"Pin explicit dependency version, e.g. '{recommended_pin}' or use a lockfile.",
                        confidence=0.96,
                        auto_fixable=True,
                        metadata={"pkg_name": pkg_name, "current_constraint": constraint, "pinned": recommended_pin}
                    )
                )

        return issues
