"""
RepoDoctor AI - ML Doctor: Validation and Reproducibility Analyzer
Audits random seed fixation, cross-validation discipline, and train/val/test splits.
"""

from __future__ import annotations

import ast

from src.core.fetcher import RepoFile, RepositoryFetcher
from src.core.models import Category, Issue, Severity


class ValidationAnalyzer:
    """Detects missing random seeds and lack of cross-validation."""

    STOCHASTIC_ESTIMATORS = {
        "RandomForestClassifier", "RandomForestRegressor", "GradientBoostingClassifier",
        "GradientBoostingRegressor", "ExtraTreesClassifier", "ExtraTreesRegressor",
        "XGBClassifier", "XGBRegressor", "LGBMClassifier", "LGBMRegressor",
        "LogisticRegression", "KMeans", "PCA", "TSNE", "train_test_split"
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> list[Issue]:
        issues: list[Issue] = []
        for pf in self.fetcher.get_python_files():
            if not pf.ast_tree:
                continue
            issues.extend(self._check_missing_random_state(pf))
            issues.extend(self._check_missing_cv(pf))
        return issues

    def _check_missing_random_state(self, pf: RepoFile) -> list[Issue]:
        """Detects calls to stochastic functions/estimators without explicit random_state/seed parameter."""
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in self.STOCHASTIC_ESTIMATORS:
                    has_seed = any(kw.arg in {"random_state", "seed"} for kw in node.keywords)
                    if not has_seed:
                        line = node.lineno
                        snippet = pf.lines[line - 1].strip() if line <= len(pf.lines) else ""
                        issues.append(
                            Issue(
                                id=f"ML-VAL-NOSEED-{abs(hash(pf.relative_path + func_name + str(line))) % 10000}",
                                category=Category.REPRODUCIBILITY,
                                title=f"Missing 'random_state' in '{func_name}()'",
                                severity=Severity.MEDIUM,
                                file_path=pf.relative_path,
                                line_number=line,
                                code_snippet=snippet,
                                risk_explanation=f"Invoking `{func_name}()` without a deterministic `random_state` causes non-reproducible splits/model weights across training runs, preventing experiment reproducibility.",
                                recommendation=f"Pass an explicit random state, e.g. `{func_name}(..., random_state=42)`.",
                                confidence=0.97,
                                auto_fixable=True,
                                metadata={"func_name": func_name}
                            )
                        )
        return issues

    def _check_missing_cv(self, pf: RepoFile) -> list[Issue]:
        """Detects machine learning scripts using a single train_test_split without cross-validation."""
        issues = []
        has_train_test_split = False
        has_cv = False

        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imp_text = ast.unparse(node)
                if "train_test_split" in imp_text:
                    has_train_test_split = True
                if any(cv_kw in imp_text for cv_kw in ["cross_val_score", "cross_validate", "KFold", "StratifiedKFold", "TimeSeriesSplit"]):
                    has_cv = True

        # If it trains models with train_test_split but no cross-validation
        if has_train_test_split and not has_cv and not pf.relative_path.startswith("tests/"):
            issues.append(
                Issue(
                    id=f"ML-VAL-NOCV-{abs(hash(pf.relative_path)) % 10000}",
                    category=Category.ML_ENGINEERING,
                    title=f"Absence of K-Fold Cross-Validation in '{pf.relative_path}'",
                    severity=Severity.LOW,
                    file_path=pf.relative_path,
                    line_number=1,
                    risk_explanation="Evaluating model metrics on a single random train/test split introduces sample-selection variance and can mask overfitting.",
                    recommendation="Validate model generalizability using `cross_val_score(model, X, y, cv=5)` or `StratifiedKFold`.",
                    confidence=0.88,
                    auto_fixable=False
                )
            )

        return issues
