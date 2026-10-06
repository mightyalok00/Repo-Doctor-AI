"""
Tests for ML Doctor Analyzers (Leakage, Preprocessing, Validation, Metrics).
"""

from src.core.fetcher import RepositoryFetcher
from src.ml_doctor.leakage import LeakageAnalyzer
from src.ml_doctor.metrics import MetricsAnalyzer
from src.ml_doctor.validation import ValidationAnalyzer


def test_data_leakage_detection():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = LeakageAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert len(issues) >= 1
    leak_issue = next((i for i in issues if "ML-LEAK-PREFIT" in i.id), None)
    assert leak_issue is not None
    assert "Data Leakage" in leak_issue.title
    assert "train_test_split" in leak_issue.title or "train_test_split" in leak_issue.code_snippet


def test_missing_random_seed_detection():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = ValidationAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert any("ML-VAL-NOSEED" in i.id for i in issues)


def test_missing_stratification_detection():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    analyzer = MetricsAnalyzer(fetcher)
    issues = analyzer.analyze()

    assert any("ML-MET-NOSTRAT" in i.id for i in issues)
