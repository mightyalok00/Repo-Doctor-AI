"""
RepoDoctor AI - Deployment and CI/CD Analyzer
Audits GitHub Actions workflows, Dockerfile best practices, docker-compose, and .gitignore hygiene.
"""

from __future__ import annotations
from typing import List
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher


class DeploymentAnalyzer:
    """Analyzes CI/CD pipelines, containerization, and repository deployment hygiene."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        issues.extend(self._check_cicd_workflows())
        issues.extend(self._check_dockerfile())
        issues.extend(self._check_gitignore())
        return issues

    def _check_cicd_workflows(self) -> List[Issue]:
        issues = []
        workflow_files = [f for f in self.fetcher.files.keys() if f.startswith(".github/workflows/") and (f.endswith(".yml") or f.endswith(".yaml"))]
        if not workflow_files:
            issues.append(
                Issue(
                    id="CICD-NOWORKFLOWS",
                    category=Category.CI_CD,
                    title="Missing Automated CI/CD Workflows",
                    severity=Severity.HIGH,
                    file_path=".github/workflows/ci.yml",
                    line_number=1,
                    risk_explanation="Repository lacks automated Continuous Integration (CI) workflows. Commits and Pull Requests are not automatically tested or linted before merging.",
                    recommendation="Add a GitHub Actions workflow `.github/workflows/ci.yml` running pytest, ruff linting, and type checks on every push and pull request.",
                    confidence=0.98,
                    auto_fixable=True
                )
            )
        return issues

    def _check_dockerfile(self) -> List[Issue]:
        issues = []
        dockerfile = self.fetcher.get_file("Dockerfile") or self.fetcher.get_file("docker/Dockerfile")
        if not dockerfile:
            issues.append(
                Issue(
                    id="DEPLOY-NODOCKER",
                    category=Category.CI_CD,
                    title="Missing Dockerfile for Containerized Deployment",
                    severity=Severity.LOW,
                    file_path="Dockerfile",
                    line_number=1,
                    risk_explanation="No Dockerfile detected. Containerization ensures reproducible deployment across development, staging, and production environments.",
                    recommendation="Add an optimized multi-stage Dockerfile with a lightweight Python base image.",
                    confidence=0.92,
                    auto_fixable=True
                )
            )
        else:
            content = dockerfile.content
            if "latest" in content and "FROM" in content:
                issues.append(
                    Issue(
                        id="DEPLOY-DOCKER-LATEST",
                        category=Category.CI_CD,
                        title="Unpinned Docker Base Image ('latest' tag)",
                        severity=Severity.MEDIUM,
                        file_path="Dockerfile",
                        line_number=1,
                        code_snippet=[l for l in dockerfile.lines if "FROM" in l][0] if dockerfile.lines else "",
                        risk_explanation="Using `FROM python:latest` creates non-deterministic Docker builds that can unexpectedly break when base image dependencies change upstream.",
                        recommendation="Pin an explicit base image tag, e.g. `FROM python:3.11-slim-bookworm`.",
                        confidence=0.96,
                        auto_fixable=True
                    )
                )
        return issues

    def _check_gitignore(self) -> List[Issue]:
        issues = []
        gitignore = self.fetcher.get_file(".gitignore")
        if not gitignore:
            issues.append(
                Issue(
                    id="DEPLOY-NOGITIGNORE",
                    category=Category.CI_CD,
                    title="Missing .gitignore File",
                    severity=Severity.HIGH,
                    file_path=".gitignore",
                    line_number=1,
                    risk_explanation="Repository lacks a .gitignore file, risking accidental commits of virtual environments, cache files, and sensitive .env files.",
                    recommendation="Add a standard Python .gitignore ignoring `.env`, `__pycache__`, `.venv`, and temporary artifacts.",
                    confidence=0.99,
                    auto_fixable=True
                )
            )
        else:
            content = gitignore.content
            essential_rules = [".env", "__pycache__", ".venv"]
            missing_rules = [r for r in essential_rules if r not in content]
            if missing_rules:
                issues.append(
                    Issue(
                        id="DEPLOY-INCOMPLETE-GITIGNORE",
                        category=Category.CI_CD,
                        title=f".gitignore Missing Essential Rules ({', '.join(missing_rules)})",
                        severity=Severity.MEDIUM,
                        file_path=".gitignore",
                        line_number=1,
                        risk_explanation=f".gitignore is missing entries for {', '.join(missing_rules)}, which may result in sensitive environment variables or bytecode being tracked.",
                        recommendation=f"Append {', '.join(missing_rules)} to .gitignore.",
                        confidence=0.97,
                        auto_fixable=True
                    )
                )
        return issues
