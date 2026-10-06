"""
RepoDoctor AI - ML Doctor: Metrics & Evaluation Analyzer
Detects missing stratification, metric-loss misalignment, and evaluation anti-patterns.
"""

from __future__ import annotations

import ast

from src.core.fetcher import RepoFile, RepositoryFetcher
from src.core.models import Category, Issue, Severity


class MetricsAnalyzer:
    """Analyzes evaluation metric choices and train_test_split stratification."""

    CLASSIFIER_NAMES = {
        "LogisticRegression", "RandomForestClassifier", "XGBClassifier",
        "LGBMClassifier", "SVC", "KNeighborsClassifier", "DecisionTreeClassifier"
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> list[Issue]:
        issues: list[Issue] = []
        for pf in self.fetcher.get_python_files():
            if not pf.ast_tree:
                continue
            issues.extend(self._check_missing_stratification(pf))
            issues.extend(self._check_imbalanced_accuracy(pf))
        return issues

    def _check_missing_stratification(self, pf: RepoFile) -> list[Issue]:
        """Detects train_test_split without stratify=y when classification models are used."""
        issues = []
        # Check if file uses classification models
        is_classification_file = False
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imp = ast.unparse(node)
                if any(clf in imp for clf in self.CLASSIFIER_NAMES):
                    is_classification_file = True

        if is_classification_file:
            for node in ast.walk(pf.ast_tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "train_test_split":
                        has_stratify = any(kw.arg == "stratify" for kw in node.keywords)
                        if not has_stratify:
                            line = node.lineno
                            snippet = pf.lines[line - 1].strip() if line <= len(pf.lines) else ""
                            issues.append(
                                Issue(
                                    id=f"ML-MET-NOSTRAT-{abs(hash(pf.relative_path + str(line))) % 10000}",
                                    category=Category.ML_ENGINEERING,
                                    title="Missing 'stratify' in Classification train_test_split()",
                                    severity=Severity.MEDIUM,
                                    file_path=pf.relative_path,
                                    line_number=line,
                                    code_snippet=snippet,
                                    risk_explanation="Splitting classification data without `stratify=y` can skew class label distributions between train and test sets, especially with imbalanced classes.",
                                    recommendation="Add `stratify=y` to `train_test_split(..., stratify=y)` to preserve identical class proportions in splits.",
                                    confidence=0.92,
                                    auto_fixable=True
                                )
                            )
        return issues

    def _check_imbalanced_accuracy(self, pf: RepoFile) -> list[Issue]:
        """Flags sole reliance on raw accuracy_score for classification without precision/recall/F1/ROC-AUC."""
        issues = []
        has_accuracy = False
        has_robust_metrics = False

        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imp = ast.unparse(node)
                if "accuracy_score" in imp:
                    has_accuracy = True
                if any(m in imp for m in ["f1_score", "roc_auc_score", "classification_report", "precision_score", "recall_score", "log_loss"]):
                    has_robust_metrics = True

        if has_accuracy and not has_robust_metrics and not pf.relative_path.startswith("tests/"):
            issues.append(
                Issue(
                    id=f"ML-MET-RAWACC-{abs(hash(pf.relative_path)) % 10000}",
                    category=Category.ML_ENGINEERING,
                    title=f"Sole Reliance on 'accuracy_score' in '{pf.relative_path}'",
                    severity=Severity.LOW,
                    file_path=pf.relative_path,
                    line_number=1,
                    risk_explanation="Evaluating classification models using only raw accuracy can be deceptively optimistic on imbalanced datasets (e.g. trivial majority class predictions).",
                    recommendation="Include `classification_report`, `f1_score(average='weighted')`, or `roc_auc_score` for multi-metric evaluation.",
                    confidence=0.89,
                    auto_fixable=False
                )
            )

        return issues
