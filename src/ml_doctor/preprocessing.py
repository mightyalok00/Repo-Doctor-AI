"""
RepoDoctor AI - ML Doctor: Preprocessing Analyzer
Audits pipeline encapsulation, transformer chaining, and feature scaling.
"""

from __future__ import annotations

import ast

from src.core.fetcher import RepoFile, RepositoryFetcher
from src.core.models import Category, Issue, Severity


class PreprocessingAnalyzer:
    """Detects missing Pipelines, unscaled inputs for distance-based estimators, and preprocessing anti-patterns."""

    DISTANCE_SENSITIVE_MODELS = {
        "LogisticRegression", "SGDClassifier", "SGDRegressor",
        "SVC", "SVR", "KNeighborsClassifier", "KNeighborsRegressor",
        "MLPClassifier", "MLPRegressor", "Ridge", "Lasso", "ElasticNet", "PCA"
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> list[Issue]:
        issues: list[Issue] = []
        for pf in self.fetcher.get_python_files():
            if not pf.ast_tree:
                continue
            issues.extend(self._check_missing_pipeline(pf))
            issues.extend(self._check_unscaled_distance_models(pf))
        return issues

    def _check_missing_pipeline(self, pf: RepoFile) -> list[Issue]:
        """Detects sequential scaler.fit_transform() + model.fit() without using sklearn Pipeline."""
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.Module)):
                has_manual_transform = False
                has_model_fit = False
                uses_pipeline = False

                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        call_repr = ast.unparse(sub)
                        if "Pipeline" in call_repr or "make_pipeline" in call_repr:
                            uses_pipeline = True
                        if isinstance(sub.func, ast.Attribute):
                            if sub.func.attr in {"fit_transform", "transform"} and "scaler" in call_repr.lower():
                                has_manual_transform = True
                            if sub.func.attr == "fit" and ("clf" in call_repr.lower() or "model" in call_repr.lower() or "reg" in call_repr.lower()):
                                has_model_fit = True

                if has_manual_transform and has_model_fit and not uses_pipeline:
                    line = getattr(node, "lineno", 1)
                    issues.append(
                        Issue(
                            id=f"ML-PREP-NOPIPE-{abs(hash(pf.relative_path + str(line))) % 10000}",
                            category=Category.ML_ENGINEERING,
                            title="Missing Scikit-Learn Pipeline Encapsulation",
                            severity=Severity.MEDIUM,
                            file_path=pf.relative_path,
                            line_number=line,
                            risk_explanation="Manual transformer chaining (`scaler.fit_transform(...)` + `model.fit(...)`) leads to fragmented preprocessing, test-time inconsistency, and errors during inference serving.",
                            recommendation="Encapsulate preprocessing and estimator in an `sklearn.pipeline.Pipeline` or `make_pipeline(StandardScaler(), Model())`.",
                            confidence=0.94,
                            auto_fixable=True
                        )
                    )
        return issues

    def _check_unscaled_distance_models(self, pf: RepoFile) -> list[Issue]:
        """Detects usage of distance/gradient sensitive models where no scaler or normalizer is imported or used."""
        issues = []
        found_models: set[str] = set()
        has_scaler = False

        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_text = ast.unparse(node)
                if any(s in import_text for s in ["Scaler", "Normalizer", "scale", "normalize"]):
                    has_scaler = True
                for model in self.DISTANCE_SENSITIVE_MODELS:
                    if model in import_text:
                        found_models.add(model)

        if found_models and not has_scaler:
            issues.append(
                Issue(
                    id=f"ML-PREP-UNSCALED-{abs(hash(pf.relative_path)) % 10000}",
                    category=Category.ML_ENGINEERING,
                    title=f"Unscaled Features with Sensitive Estimator ({', '.join(found_models)})",
                    severity=Severity.HIGH,
                    file_path=pf.relative_path,
                    line_number=1,
                    risk_explanation=f"Estimator(s) {', '.join(found_models)} rely on Euclidean distance or gradient descent. Features with larger raw magnitudes will dominate coefficients without proper standard scaling.",
                    recommendation="Apply `StandardScaler` or `RobustScaler` before fitting distance/gradient sensitive estimators.",
                    confidence=0.91,
                    auto_fixable=False
                )
            )
        return issues
