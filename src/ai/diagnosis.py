"""
RepoDoctor AI - Diagnosis and Scorecard Engine
Coordinates all static & ML analyzers, synthesizes findings, and calculates calibrated scores.
"""

from __future__ import annotations

from src.analyzer.architecture import ArchitectureAnalyzer
from src.analyzer.code_quality import CodeQualityAnalyzer
from src.analyzer.dependencies import DependencyAnalyzer
from src.analyzer.deployment import DeploymentAnalyzer
from src.analyzer.documentation import DocumentationAnalyzer
from src.analyzer.security import SecurityAnalyzer
from src.analyzer.testing import TestingAnalyzer
from src.core.fetcher import RepositoryFetcher
from src.core.models import (
    Category,
    CategoryScore,
    Issue,
    RepositoryDiagnosis,
    RepositoryScorecard,
    Severity,
)
from src.ml_doctor.leakage import LeakageAnalyzer
from src.ml_doctor.metrics import MetricsAnalyzer
from src.ml_doctor.preprocessing import PreprocessingAnalyzer
from src.ml_doctor.validation import ValidationAnalyzer


class DiagnosisEngine:
    """Orchestrates comprehensive repository inspection and computes weighted scorecard."""

    SEVERITY_DEDUCTIONS = {
        Severity.CRITICAL: 2.5,
        Severity.HIGH: 1.5,
        Severity.MEDIUM: 0.8,
        Severity.LOW: 0.3,
        Severity.INFO: 0.0
    }

    CATEGORY_WEIGHTS = {
        Category.ARCHITECTURE.value: 0.12,
        Category.CODE_QUALITY.value: 0.15,
        Category.TESTING.value: 0.15,
        Category.ML_ENGINEERING.value: 0.20,
        Category.SECURITY.value: 0.15,
        Category.DOCUMENTATION.value: 0.08,
        Category.REPRODUCIBILITY.value: 0.08,
        Category.CI_CD.value: 0.07,
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def run_full_diagnosis(self) -> RepositoryDiagnosis:
        """Run all analyzers and aggregate findings into a complete repository diagnosis."""
        all_issues: list[Issue] = []

        analyzers = [
            ArchitectureAnalyzer(self.fetcher),
            CodeQualityAnalyzer(self.fetcher),
            DependencyAnalyzer(self.fetcher),
            SecurityAnalyzer(self.fetcher),
            TestingAnalyzer(self.fetcher),
            DocumentationAnalyzer(self.fetcher),
            DeploymentAnalyzer(self.fetcher),
            LeakageAnalyzer(self.fetcher),
            PreprocessingAnalyzer(self.fetcher),
            ValidationAnalyzer(self.fetcher),
            MetricsAnalyzer(self.fetcher),
        ]

        for analyzer in analyzers:
            try:
                issues = analyzer.analyze()
                all_issues.extend(issues)
            except Exception:
                # Keep diagnosing even if a specific sub-analyzer hits an edge case
                pass

        # Calculate scores
        scorecard = self._compute_scorecard(all_issues)

        # Count metadata
        py_files = self.fetcher.get_python_files()
        total_loc = sum(f.loc for f in self.fetcher.files.values())

        # Generate summary
        summary = self._generate_executive_summary(scorecard, all_issues)

        return RepositoryDiagnosis(
            repo_name=self.fetcher.repo_name,
            repo_path=str(self.fetcher.repo_path),
            total_files=len(self.fetcher.files),
            python_files=len(py_files),
            total_loc=total_loc,
            scorecard=scorecard,
            issues=all_issues,
            patches=[],
            validation_results=[],
            health_timeline=[],
            executive_summary=summary
        )

    def _compute_scorecard(self, issues: list[Issue]) -> RepositoryScorecard:
        # Group issues by category
        cat_issues: dict[str, list[Issue]] = {c.value: [] for c in Category}
        for issue in issues:
            cat_val = issue.category.value if isinstance(issue.category, Category) else str(issue.category)
            if cat_val in cat_issues:
                cat_issues[cat_val].append(issue)

        breakdown: list[CategoryScore] = []
        category_scores: dict[str, float] = {}

        for cat in Category:
            c_val = cat.value
            cat_list = cat_issues.get(c_val, [])
            deduction = sum(self.SEVERITY_DEDUCTIONS.get(iss.severity, 0.5) for iss in cat_list)
            score = max(1.0, min(10.0, 10.0 - deduction))
            score = round(score, 1)

            crit_count = sum(1 for i in cat_list if i.severity == Severity.CRITICAL)
            summary_msg = "Excellent health" if score >= 9.0 else "Minor issues found" if score >= 7.0 else "Needs immediate attention"

            cat_score_obj = CategoryScore(
                category=cat,
                score=score,
                issue_count=len(cat_list),
                critical_count=crit_count,
                summary=summary_msg
            )
            breakdown.append(cat_score_obj)
            category_scores[c_val] = score

        # Compute weighted overall score
        weighted_sum = sum(category_scores.get(c.value, 10.0) * self.CATEGORY_WEIGHTS.get(c.value, 0.1) for c in Category)
        overall_score = round(max(1.0, min(10.0, weighted_sum)), 1)

        # Severity counts
        crit_tot = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        high_tot = sum(1 for i in issues if i.severity == Severity.HIGH)
        med_tot = sum(1 for i in issues if i.severity == Severity.MEDIUM)
        low_tot = sum(1 for i in issues if i.severity == Severity.LOW)

        grade = "A+" if overall_score >= 9.5 else "A" if overall_score >= 8.5 else "B" if overall_score >= 7.0 else "C" if overall_score >= 5.5 else "D" if overall_score >= 4.0 else "F"

        return RepositoryScorecard(
            overall_score=overall_score,
            category_scores=category_scores,
            breakdown=breakdown,
            total_issues=len(issues),
            critical_issues=crit_tot,
            high_issues=high_tot,
            medium_issues=med_tot,
            low_issues=low_tot,
            grade=grade
        )

    def _generate_executive_summary(self, scorecard: RepositoryScorecard, issues: list[Issue]) -> str:
        crit_issues = [i for i in issues if i.severity == Severity.CRITICAL]
        high_issues = [i for i in issues if i.severity == Severity.HIGH]

        lines = [
            f"Repository scored **{scorecard.overall_score}/10** (Grade: **{scorecard.grade}**) across 8 engineering dimensions.",
            f"Found **{scorecard.total_issues} total issues** ({scorecard.critical_issues} Critical, {scorecard.high_issues} High, {scorecard.medium_issues} Medium)."
        ]

        if crit_issues:
            lines.append(f"🚨 **Critical Attention Required**: {crit_issues[0].title} in `{crit_issues[0].file_path}`.")
        elif high_issues:
            lines.append(f"⚠️ **Key Risk**: {high_issues[0].title} in `{high_issues[0].file_path}`.")
        else:
            lines.append("✨ Repository demonstrates strong software engineering hygiene with no blocking critical vulnerabilities.")

        return " ".join(lines)
