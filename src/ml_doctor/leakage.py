"""
RepoDoctor AI - ML Doctor: Data & Target Leakage Analyzer
Detects pre-split fitting, target leakage, and train/test contamination anti-patterns via AST analysis.
"""

from __future__ import annotations
import ast
from typing import List, Dict, Set, Tuple
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher, RepoFile


class LeakageAnalyzer:
    """Analyzes AST trees for ML data leakage and preprocessing contamination."""

    SCALERS_AND_TRANSFORMERS = {
        "StandardScaler", "MinMaxScaler", "RobustScaler", "Normalizer",
        "SimpleImputer", "KNNImputer", "OneHotEncoder", "OrdinalEncoder",
        "TargetEncoder", "PCA", "QuantileTransformer", "PowerTransformer"
    }

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        for pf in self.fetcher.get_python_files():
            if not pf.ast_tree:
                continue
            issues.extend(self._check_fit_before_split(pf))
            issues.extend(self._check_fit_on_test_data(pf))
        return issues

    def _check_fit_before_split(self, pf: RepoFile) -> List[Issue]:
        """
        Detects cases where a transformer (e.g. StandardScaler) has .fit() or .fit_transform()
        called on full dataset (X or df) BEFORE train_test_split() is called.
        """
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                body_nodes = getattr(node, "body", [])
                
                fit_calls: List[Tuple[int, str, str]] = [] # (line_number, transformer_name, call_snippet)
                split_line = None

                for item in body_nodes:
                    # Look for transformer fitting
                    for sub in ast.walk(item):
                        if isinstance(sub, ast.Call):
                            # Check fit or fit_transform
                            if isinstance(sub.func, ast.Attribute) and sub.func.attr in {"fit", "fit_transform"}:
                                # Check if called on X or full dataset
                                line = sub.lineno
                                snippet = pf.lines[line - 1].strip() if line <= len(pf.lines) else ""
                                fit_calls.append((line, sub.func.attr, snippet))
                            
                            # Check train_test_split call
                            if isinstance(sub.func, ast.Name) and sub.func.id == "train_test_split":
                                split_line = sub.lineno

                # If fit_transform / fit occurred BEFORE train_test_split
                if split_line and fit_calls:
                    for f_line, f_attr, f_snip in fit_calls:
                        if f_line < split_line:
                            issues.append(
                                Issue(
                                    id=f"ML-LEAK-PREFIT-{abs(hash(pf.relative_path + str(f_line))) % 10000}",
                                    category=Category.ML_ENGINEERING,
                                    title="Data Leakage: Preprocessing Fitted Before train_test_split()",
                                    severity=Severity.CRITICAL,
                                    file_path=pf.relative_path,
                                    line_number=f_line,
                                    end_line_number=split_line,
                                    code_snippet=f"{f_snip}\n...\n{pf.lines[split_line - 1].strip() if split_line <= len(pf.lines) else ''}",
                                    risk_explanation="Transformer (scaler/imputer/encoder) is fitted on the entire dataset prior to splitting. Test set statistics (mean, variance, category frequencies) contaminate the training preprocessing pipeline, causing artificially inflated evaluation metrics and real-world performance degradation.",
                                    recommendation="Fit transformers ONLY on training data (`scaler.fit(X_train)` or wrap in `sklearn.pipeline.Pipeline`). Use `.transform(X_test)` on test data.",
                                    confidence=0.98,
                                    auto_fixable=True,
                                    metadata={"fit_line": f_line, "split_line": split_line}
                                )
                            )
        return issues

    def _check_fit_on_test_data(self, pf: RepoFile) -> List[Issue]:
        """Detects scaler.fit() or scaler.fit_transform() directly invoked on test sets (X_test, test_df)."""
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in {"fit", "fit_transform"}:
                    if node.args:
                        first_arg = ast.unparse(node.args[0]).lower()
                        if "test" in first_arg or "val" in first_arg:
                            line = node.lineno
                            issues.append(
                                Issue(
                                    id=f"ML-LEAK-TESTFIT-{abs(hash(pf.relative_path + str(line))) % 10000}",
                                    category=Category.ML_ENGINEERING,
                                    title=f"Test-Set Contamination: Calling '{node.func.attr}()' on Test Data",
                                    severity=Severity.CRITICAL,
                                    file_path=pf.relative_path,
                                    line_number=line,
                                    code_snippet=pf.lines[line - 1].strip() if line <= len(pf.lines) else "",
                                    risk_explanation=f"Calling `{node.func.attr}()` on validation/test data recalculates preprocessing parameters on unseen data instead of using the learned training parameters, violating the evaluation contract.",
                                    recommendation="Call `.transform()` on test/validation sets rather than `.fit()` or `.fit_transform()`.",
                                    confidence=0.99,
                                    auto_fixable=True
                                )
                            )
        return issues
