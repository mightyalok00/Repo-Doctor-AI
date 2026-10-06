"""
RepoDoctor AI - Test Suite and Coverage Analyzer
Audits test coverage, test-to-code ratio, missing unit tests, and assertion health.
"""

from __future__ import annotations

import ast

from src.core.fetcher import RepositoryFetcher
from src.core.models import Category, Issue, Severity


class TestingAnalyzer:
    """Evaluates test coverage, test-to-code ratio, and tests quality."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> list[Issue]:
        issues: list[Issue] = []
        py_files = self.fetcher.get_python_files()
        if not py_files:
            return issues

        test_files = [f for f in py_files if "test" in f.relative_path.lower() or f.relative_path.startswith("tests/")]
        src_files = [f for f in py_files if f not in test_files]

        # Check if tests exist at all
        if not test_files and src_files:
            issues.append(
                Issue(
                    id="TEST-NOTESTS",
                    category=Category.TESTING,
                    title="No Automated Test Suite Detected",
                    severity=Severity.CRITICAL,
                    file_path=src_files[0].relative_path if src_files else "tests/",
                    line_number=1,
                    risk_explanation="Repository has no test directory or test files (`test_*.py`). Automated verification of correctness, regression detection, and CI validation are impossible.",
                    recommendation="Initialize a 'tests/' directory with pytest test suites covering core functions and pipelines.",
                    confidence=0.99,
                    auto_fixable=True
                )
            )
            return issues

        # Analyze test-to-code ratio
        total_src_loc = sum(f.loc for f in src_files)
        total_test_loc = sum(f.loc for f in test_files)
        test_ratio = total_test_loc / max(1, total_src_loc)

        if test_ratio < 0.15 and total_src_loc > 100:
            issues.append(
                Issue(
                    id="TEST-LOWRATIO",
                    category=Category.TESTING,
                    title=f"Low Test-to-Code Ratio ({test_ratio:.1%})",
                    severity=Severity.HIGH if test_ratio < 0.05 else Severity.MEDIUM,
                    file_path=test_files[0].relative_path if test_files else "tests/",
                    risk_explanation=f"Test code accounts for only {test_ratio:.1%} of total source code ({total_test_loc} test LOC vs {total_src_loc} source LOC). Production-grade systems typically maintain >30-50% test ratio.",
                    recommendation="Expand unit test coverage with pytest fixtures and parameterized test cases.",
                    confidence=0.92,
                    auto_fixable=False
                )
            )

        # Check for empty tests / tests with no assertions
        for tf in test_files:
            if not tf.ast_tree:
                continue
            for node in ast.walk(tf.ast_tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    has_assert = any(isinstance(subnode, (ast.Assert, ast.Call)) for subnode in ast.walk(node))
                    if not has_assert:
                        issues.append(
                            Issue(
                                id=f"TEST-NOASSERT-{abs(hash(tf.relative_path + node.name)) % 10000}",
                                category=Category.TESTING,
                                title=f"Test Without Assertions in '{node.name}()'",
                                severity=Severity.MEDIUM,
                                file_path=tf.relative_path,
                                line_number=node.lineno,
                                risk_explanation=f"Test function '{node.name}' executes code without asserting expected invariants, giving a false sense of test pass confidence.",
                                recommendation="Add explicit `assert` statements verifying returned values, states, or raised exceptions.",
                                confidence=0.95,
                                auto_fixable=True
                            )
                        )

        return issues
