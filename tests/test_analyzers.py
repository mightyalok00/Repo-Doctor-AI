"""
Tests for Core Analyzers (Security, Code Quality, Dependencies, Documentation, Deployment).
"""

import pytest
from src.core.fetcher import RepositoryFetcher
from src.analyzer.security import SecurityAnalyzer
from src.analyzer.code_quality import CodeQualityAnalyzer
from src.analyzer.dependencies import DependencyAnalyzer
from src.analyzer.documentation import DocumentationAnalyzer
from src.analyzer.deployment import DeploymentAnalyzer
from src.ai.diagnosis import DiagnosisEngine


def test_security_eval_detection():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = SecurityAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert any("SEC-EXEC" in i.id for i in issues)


def test_code_quality_mutable_default():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = CodeQualityAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert any("QUAL-MUT" in i.id for i in issues)
    assert any("QUAL-EXC" in i.id for i in issues)


def test_dependency_unpinned_and_deprecated():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = DependencyAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert any("DEP-UNPIN" in i.id for i in issues)
    assert any("DEP-DEPR-sklearn" in i.id for i in issues)


def test_full_diagnosis_scorecard():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    assert diagnosis.scorecard.overall_score > 0.0
    assert len(diagnosis.issues) >= 5
    assert diagnosis.scorecard.grade in ["A+", "A", "B", "C", "D", "F"]
