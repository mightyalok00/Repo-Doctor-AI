"""
RepoDoctor AI - Code Quality Analyzer
Evaluates AST patterns, swallowed exceptions, mutable defaults, complexity, and type annotations.
"""

from __future__ import annotations
import ast
from typing import List, Optional
from src.core.models import Issue, Category, Severity
from src.core.fetcher import RepositoryFetcher, RepoFile


class CyclomaticComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)


class CodeQualityAnalyzer:
    """Analyzes AST-level code quality anti-patterns and maintainability issues."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> List[Issue]:
        issues: List[Issue] = []
        for pf in self.fetcher.get_python_files():
            if not pf.ast_tree:
                continue
            issues.extend(self._check_swallowed_exceptions(pf))
            issues.extend(self._check_mutable_defaults(pf))
            issues.extend(self._check_function_complexity(pf))
            issues.extend(self._check_type_hints(pf))
        return issues

    def _get_snippet(self, pf: RepoFile, start_line: int, end_line: Optional[int] = None) -> str:
        end = end_line or start_line
        if 1 <= start_line <= len(pf.lines):
            return "\n".join(pf.lines[start_line - 1: min(end, len(pf.lines))])
        return ""

    def _check_swallowed_exceptions(self, pf: RepoFile) -> List[Issue]:
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, ast.ExceptHandler):
                # Check for bare except: or except Exception: pass / continue
                is_swallowed = False
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Continue)):
                    is_swallowed = True

                if is_swallowed:
                    line = node.lineno
                    snippet = self._get_snippet(pf, line, line + 2)
                    issues.append(
                        Issue(
                            id=f"QUAL-EXC-{abs(hash(pf.relative_path + str(line))) % 10000}",
                            category=Category.CODE_QUALITY,
                            title="Silent Exception Swallowing (except: pass)",
                            severity=Severity.HIGH,
                            file_path=pf.relative_path,
                            line_number=line,
                            code_snippet=snippet,
                            risk_explanation="Silently swallowing exceptions hides critical runtime bugs, unexpected data corruptions, and breaks debuggability.",
                            recommendation="Catch specific exception types and log errors appropriately using a logger (e.g., logger.warning or logger.exception).",
                            confidence=0.98,
                            auto_fixable=True,
                            metadata={"handler_type": "swallowed_exception"}
                        )
                    )
        return issues

    def _check_mutable_defaults(self, pf: RepoFile) -> List[Issue]:
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        line = node.lineno
                        snippet = self._get_snippet(pf, line, line + 2)
                        issues.append(
                            Issue(
                                id=f"QUAL-MUT-{abs(hash(pf.relative_path + node.name + str(line))) % 10000}",
                                category=Category.CODE_QUALITY,
                                title=f"Mutable Default Argument in '{node.name}()'",
                                severity=Severity.MEDIUM,
                                file_path=pf.relative_path,
                                line_number=line,
                                code_snippet=snippet,
                                risk_explanation="Default argument is instantiated once at function definition time. Mutations inside the function persist across calls, causing subtle shared state bugs.",
                                recommendation=f"Use 'None' as default value (e.g., arg: Optional[list] = None) and initialize inside the function body.",
                                confidence=0.99,
                                auto_fixable=True,
                                metadata={"func_name": node.name}
                            )
                        )
        return issues

    def _check_function_complexity(self, pf: RepoFile) -> List[Issue]:
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visitor = CyclomaticComplexityVisitor()
                visitor.visit(node)
                if visitor.complexity > 12:
                    line = node.lineno
                    issues.append(
                        Issue(
                            id=f"QUAL-CMPX-{abs(hash(pf.relative_path + node.name)) % 10000}",
                            category=Category.CODE_QUALITY,
                            title=f"High Cyclomatic Complexity ({visitor.complexity}) in '{node.name}'",
                            severity=Severity.HIGH if visitor.complexity > 20 else Severity.MEDIUM,
                            file_path=pf.relative_path,
                            line_number=line,
                            code_snippet=self._get_snippet(pf, line, min(line + 10, pf.loc)),
                            risk_explanation=f"Function '{node.name}' has a cyclomatic complexity of {visitor.complexity}. Excess branching paths significantly increase defect rates and make comprehensive unit testing difficult.",
                            recommendation="Decompose this function into smaller, single-purpose helper functions or apply the strategy pattern.",
                            confidence=0.92,
                            auto_fixable=False
                        )
                    )
        return issues

    def _check_type_hints(self, pf: RepoFile) -> List[Issue]:
        issues = []
        if pf.relative_path.startswith("tests/") or pf.relative_path.startswith("test_"):
            return issues

        public_funcs = 0
        untyped_funcs = 0

        for node in ast.walk(pf.ast_tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    public_funcs += 1
                    # Check return annotation or arguments
                    has_arg_types = any(arg.annotation is not None for arg in node.args.args if arg.arg != "self")
                    has_ret_type = node.returns is not None
                    if not (has_arg_types or has_ret_type):
                        untyped_funcs += 1

        if public_funcs >= 4 and (untyped_funcs / public_funcs) > 0.65:
            issues.append(
                Issue(
                    id=f"QUAL-TYPE-{abs(hash(pf.relative_path)) % 10000}",
                    category=Category.CODE_QUALITY,
                    title=f"Missing Type Annotations in '{pf.relative_path}' ({untyped_funcs}/{public_funcs} functions)",
                    severity=Severity.LOW,
                    file_path=pf.relative_path,
                    line_number=1,
                    code_snippet=f"# {untyped_funcs} untyped public functions in {pf.relative_path}",
                    risk_explanation="Lack of PEP 484 type annotations reduces IDE autocomplete reliability, prevents static type checking (e.g. Pyright/Mypy), and increases runtime type mismatch defects.",
                    recommendation="Add explicit parameter and return type hints to public functions and classes.",
                    confidence=0.90,
                    auto_fixable=False
                )
            )
        return issues
