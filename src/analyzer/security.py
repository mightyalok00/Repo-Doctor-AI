"""
RepoDoctor AI - Security Vulnerability Analyzer
Performs AST and regex-based scanning for dangerous functions, SQL injection, secrets, and insecure loads.
"""

from __future__ import annotations

import ast
import re

from src.core.fetcher import RepoFile, RepositoryFetcher
from src.core.models import Category, Issue, Severity


class SecurityAnalyzer:
    """Detects security vulnerabilities, hardcoded secrets, injection vectors, and unsafe calls."""

    # Secret patterns regex
    SECRET_PATTERNS = [
        (re.compile(r"""(?i)(?:api_key|apikey|secret_key|auth_token|access_token|aws_secret_access_key|password)\s*=\s*['"][a-zA-Z0-9_\-\.]{12,}['"]"""), "Hardcoded Secret / API Token"),
        (re.compile(r"""ghp_[a-zA-Z0-9]{36}"""), "Exposed GitHub Personal Access Token"),
        (re.compile(r"""sk-[a-zA-Z0-9]{32,48}"""), "Exposed OpenAI Secret Key"),
        (re.compile(r"""AKIA[0-9A-Z]{16}"""), "Exposed AWS Access Key ID")
    ]

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def analyze(self) -> list[Issue]:
        issues: list[Issue] = []
        for pf in self.fetcher.get_python_files():
            issues.extend(self._scan_secrets(pf))
            if pf.ast_tree:
                issues.extend(self._scan_dangerous_ast_calls(pf))
                issues.extend(self._scan_sql_injection(pf))
        return issues

    def _scan_secrets(self, pf: RepoFile) -> list[Issue]:
        issues = []
        for idx, line in enumerate(pf.lines, start=1):
            # Skip test files containing dummy mock strings
            if "test" in pf.relative_path.lower() and ("dummy" in line.lower() or "example" in line.lower() or "mock" in line.lower()):
                continue

            for pattern, name in self.SECRET_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        Issue(
                            id=f"SEC-SECRET-{abs(hash(pf.relative_path + str(idx))) % 10000}",
                            category=Category.SECURITY,
                            title=f"{name} Detected in Source Code",
                            severity=Severity.CRITICAL,
                            file_path=pf.relative_path,
                            line_number=idx,
                            code_snippet=line.strip()[:80] + "...",
                            risk_explanation="Hardcoding secrets in version control exposes production credentials to leakages, unauthorized access, and supply chain compromise.",
                            recommendation="Move sensitive credentials to environment variables (`os.getenv(...)`) and load them via `.env` file.",
                            confidence=0.97,
                            auto_fixable=True,
                            metadata={"pattern": name}
                        )
                    )
        return issues

    def _scan_dangerous_ast_calls(self, pf: RepoFile) -> list[Issue]:
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, ast.Call):
                # Check for eval() and exec()
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    line = node.lineno
                    issues.append(
                        Issue(
                            id=f"SEC-EXEC-{abs(hash(pf.relative_path + str(line))) % 10000}",
                            category=Category.SECURITY,
                            title=f"Arbitrary Code Execution via '{node.func.id}()'",
                            severity=Severity.CRITICAL,
                            file_path=pf.relative_path,
                            line_number=line,
                            code_snippet=pf.lines[line - 1].strip() if line <= len(pf.lines) else "",
                            risk_explanation=f"Using '{node.func.id}()' evaluates arbitrary string input as Python code, creating severe remote code execution (RCE) vulnerabilities.",
                            recommendation=f"Refactor to avoid '{node.func.id}()'. Use `ast.literal_eval()` for safe literal parsing or structured data parsing (json).",
                            confidence=0.99,
                            auto_fixable=True,
                            metadata={"func": node.func.id}
                        )
                    )

                # Check for yaml.load(..., Loader=None)
                if isinstance(node.func, ast.Attribute) and node.func.attr == "load":
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in {"yaml", "pyyaml"}:
                        has_safe_loader = any(kw.arg == "Loader" and "SafeLoader" in ast.unparse(kw.value) for kw in node.keywords)
                        if not has_safe_loader:
                            line = node.lineno
                            issues.append(
                                Issue(
                                    id=f"SEC-YAML-{abs(hash(pf.relative_path + str(line))) % 10000}",
                                    category=Category.SECURITY,
                                    title="Unsafe YAML Deserialization (yaml.load)",
                                    severity=Severity.HIGH,
                                    file_path=pf.relative_path,
                                    line_number=line,
                                    code_snippet=pf.lines[line - 1].strip() if line <= len(pf.lines) else "",
                                    risk_explanation="Calling `yaml.load()` without `SafeLoader` can instantiate arbitrary Python objects and execute arbitrary code during parsing.",
                                    recommendation="Use `yaml.safe_load(...)` instead.",
                                    confidence=0.98,
                                    auto_fixable=True
                                )
                            )

                # Check for subprocess.Popen / run with shell=True
                if isinstance(node.func, ast.Attribute) and node.func.attr in {"Popen", "run", "call", "check_output"}:
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            line = node.lineno
                            issues.append(
                                Issue(
                                    id=f"SEC-SHELL-{abs(hash(pf.relative_path + str(line))) % 10000}",
                                    category=Category.SECURITY,
                                    title="Subprocess Execution with 'shell=True'",
                                    severity=Severity.HIGH,
                                    file_path=pf.relative_path,
                                    line_number=line,
                                    code_snippet=pf.lines[line - 1].strip() if line <= len(pf.lines) else "",
                                    risk_explanation="Using `shell=True` passes command strings to system shell, exposing the application to command injection attacks if arguments contain untrusted inputs.",
                                    recommendation="Pass arguments as a list of arguments without `shell=True` (e.g. `subprocess.run(['command', arg1, arg2])`).",
                                    confidence=0.95,
                                    auto_fixable=True
                                )
                            )
        return issues

    def _scan_sql_injection(self, pf: RepoFile) -> list[Issue]:
        issues = []
        for node in ast.walk(pf.ast_tree):
            if isinstance(node, ast.JoinedStr):  # f-string
                # Check if it looks like a SQL query
                sql_keywords = ["select ", "insert into ", "update ", "delete from "]
                raw_text = "".join(part.value for part in node.values if isinstance(part, ast.Constant)).lower()
                if any(kw in raw_text for kw in sql_keywords):
                    line = node.lineno
                    issues.append(
                        Issue(
                            id=f"SEC-SQL-{abs(hash(pf.relative_path + str(line))) % 10000}",
                            category=Category.SECURITY,
                            title="Potential SQL Injection via String Interpolation",
                            severity=Severity.HIGH,
                            file_path=pf.relative_path,
                            line_number=line,
                            code_snippet=pf.lines[line - 1].strip() if line <= len(pf.lines) else "",
                            risk_explanation="Constructing SQL statements dynamically with f-strings or string concatenation bypasses database query parameterization and allows SQL injection.",
                            recommendation="Use parameterized queries / prepared statements (e.g., `cursor.execute('SELECT * FROM t WHERE id = ?', (val,))`).",
                            confidence=0.91,
                            auto_fixable=False
                        )
                    )
        return issues
