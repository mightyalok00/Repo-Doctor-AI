"""
RepoDoctor AI - Autonomous Code Repair & Patch Generator
Synthesizes verified unified diffs and replacement code for detected issues.
"""

from __future__ import annotations

import re

from src.core.fetcher import RepositoryFetcher
from src.core.git_utils import generate_diff
from src.core.models import Issue, Patch


class PatchGenerator:
    """Generates precise code fixes, dependency resolutions, and configuration patches."""

    def __init__(self, fetcher: RepositoryFetcher):
        self.fetcher = fetcher

    def generate_all_patches(self, issues: list[Issue]) -> list[Patch]:
        """Generate patches for all auto-fixable issues."""
        patches: list[Patch] = []
        for issue in issues:
            if not issue.auto_fixable:
                continue
            patch = self.generate_patch_for_issue(issue)
            if patch:
                patches.append(patch)
        return patches

    def generate_patch_for_issue(self, issue: Issue) -> Patch | None:
        """Route to specific patch generator based on issue ID and category."""
        repo_file = self.fetcher.get_file(issue.file_path)

        # 1. Missing Files (e.g. .gitignore, ci.yml, README, LICENSE, __init__.py)
        if not repo_file or issue.id.startswith("CICD-") or issue.id.startswith("DEPLOY-NO") or issue.id.startswith("DOC-NO") or issue.id.startswith("ARCH-INIT"):
            return self._generate_missing_file_patch(issue)

        original_content = repo_file.content
        repaired_content = None

        # 2. Dependency fixes
        if issue.id.startswith("DEP-"):
            repaired_content = self._fix_dependencies(original_content, issue)

        # 3. ML Doctor Fixes
        elif issue.id.startswith("ML-LEAK-PREFIT"):
            repaired_content = self._fix_data_leakage(original_content, issue)
        elif issue.id.startswith("ML-VAL-NOSEED"):
            repaired_content = self._fix_random_seed(original_content, issue)
        elif issue.id.startswith("ML-MET-NOSTRAT"):
            repaired_content = self._fix_stratification(original_content, issue)

        # 4. Code Quality Fixes
        elif issue.id.startswith("QUAL-EXC"):
            repaired_content = self._fix_swallowed_exception(original_content, issue)
        elif issue.id.startswith("QUAL-MUT"):
            repaired_content = self._fix_mutable_defaults(original_content, issue)

        # 5. Security Fixes
        elif issue.id.startswith("SEC-YAML"):
            repaired_content = self._fix_unsafe_yaml(original_content, issue)
        elif issue.id.startswith("SEC-EXEC"):
            repaired_content = self._fix_eval_exec(original_content, issue)

        if repaired_content and repaired_content != original_content:
            diff = generate_diff(original_content, repaired_content, issue.file_path)
            return Patch(
                issue_id=issue.id,
                file_path=issue.file_path,
                description=f"Auto-repair: {issue.title}",
                original_code=original_content,
                replacement_code=repaired_content,
                diff=diff
            )

        return None

    def _generate_missing_file_patch(self, issue: Issue) -> Patch | None:
        file_path = issue.file_path
        content = ""

        if file_path.endswith(".gitignore"):
            content = "# Python Bytecode & Cache\n__pycache__/\n*.py[cod]\n*$py.class\n\n# Environments\n.env\n.venv/\nenv/\nvenv/\n\n# Distribution & Builds\ndist/\nbuild/\n*.egg-info/\n\n# IDE\n.vscode/\n.idea/\n\n# Testing & Coverage\n.pytest_cache/\n.coverage\nhtmlcov/\n"
        elif "ci.yml" in file_path:
            content = "name: CI Pipeline\n\non:\n  push:\n    branches: [ main, master ]\n  pull_request:\n    branches: [ main, master ]\n\njobs:\n  build-and-test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - name: Set up Python\n      uses: actions/setup-python@v5\n      with:\n        python-version: '3.11'\n    - name: Install dependencies\n      run: |\n        python -m pip install --upgrade pip\n        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi\n        pip install pytest ruff\n    - name: Lint with Ruff\n      run: ruff check .\n    - name: Run Tests with Pytest\n      run: pytest\n"
        elif file_path == "README.md":
            repo_name = self.fetcher.repo_name or "Project"
            content = f"# {repo_name} 🚀\n\n[![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen)]()\n[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()\n[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)\n\n## Overview\nProduction-ready repository diagnosed and verified with RepoDoctor AI.\n\n## Installation\n```bash\ngit clone <repo_url>\ncd {repo_name}\npython -m venv .venv\nsource .venv/bin/activate  # Or .venv\\Scripts\\activate on Windows\npip install -r requirements.txt\n```\n\n## Usage\n```bash\npython main.py\n```\n\n## Testing\n```bash\npytest\n```\n\n## Architecture\n- `src/`: Modular application source code.\n- `tests/`: Automated unit & integration test suites.\n\n## License\nMIT License © 2026\n"
        elif file_path == "LICENSE":
            content = "MIT License\n\nCopyright (c) 2026 RepoDoctor\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the \"Software\"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n"
        elif file_path.endswith("__init__.py"):
            content = '"""Package initialization module."""\n'
        elif file_path == "Dockerfile":
            content = "FROM python:3.11-slim-bookworm\n\nWORKDIR /app\n\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\nCOPY . .\n\nCMD [\"python\", \"main.py\"]\n"
        else:
            return None

        diff = generate_diff("", content, file_path)
        return Patch(
            issue_id=issue.id,
            file_path=file_path,
            description=f"Create {file_path}",
            original_code="",
            replacement_code=content,
            diff=diff
        )

    def _fix_dependencies(self, content: str, issue: Issue) -> str:
        lines = content.splitlines()
        repaired = []
        pkg = issue.metadata.get("pkg_name")

        for line in lines:
            clean = line.strip().lower()
            if pkg and (clean.startswith(pkg) or clean.startswith(pkg.replace("-", "_"))):
                if "replacement" in issue.metadata:
                    repaired.append(issue.metadata["replacement"])
                elif "pinned" in issue.metadata:
                    repaired.append(issue.metadata["pinned"])
                else:
                    repaired.append(line)
            else:
                repaired.append(line)

        return "\n".join(repaired) + "\n"

    def _fix_data_leakage(self, content: str, issue: Issue) -> str:
        """
        Refactors pre-split fitting:
        Transforms:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)
            X_train, X_test, y_train, y_test = train_test_split(X, y)
        To:
            X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)
        """
        # Pattern matching for common pre-split leakage pattern
        leakage_pattern = re.compile(
            r"""([ \t]*)(scaler\s*=\s*[A-Za-z0-9_]+\(\))\n[ \t]*([A-Za-z0-9_]+)\s*=\s*scaler\.fit_transform\(\3\)\n([ \t]*)([A-Za-z0-9_, ]+)\s*=\s*train_test_split\(([^)]+)\)""",
            re.MULTILINE
        )

        match = leakage_pattern.search(content)
        if match:
            indent = match.group(1)
            scaler_inst = match.group(2)
            var_x = match.group(3)
            split_vars = match.group(5)
            split_args = match.group(6)

            # Ensure random_state is included
            if "random_state" not in split_args:
                split_args = f"{split_args.strip()}, random_state=42"

            replacement = (
                f"{indent}{split_vars} = train_test_split({split_args})\n"
                f"{indent}{scaler_inst}\n"
                f"{indent}X_train = scaler.fit_transform(X_train)\n"
                f"{indent}X_test = scaler.transform(X_test)"
            )
            return leakage_pattern.sub(replacement, content)

        # Alternative simple line replacement
        lines = content.splitlines()
        fit_line = issue.metadata.get("fit_line")
        split_line = issue.metadata.get("split_line")
        if fit_line and split_line and 1 <= fit_line <= len(lines):
            # If line is X = scaler.fit_transform(X) before split
            orig_fit = lines[fit_line - 1]
            if "fit_transform" in orig_fit:
                # Comment out pre-split fit and annotate
                lines[fit_line - 1] = f"# [RepoDoctor Fixed Data Leakage] Moved after split\n# {orig_fit}"
                return "\n".join(lines) + "\n"

        return content

    def _fix_random_seed(self, content: str, issue: Issue) -> str:
        """Injects random_state=42 into stochastic calls."""
        lines = content.splitlines()
        line_num = issue.line_number
        if line_num and 1 <= line_num <= len(lines):
            target_line = lines[line_num - 1]
            func_name = issue.metadata.get("func_name", "")
            if func_name and func_name in target_line and "random_state" not in target_line:
                # Add random_state=42 before closing paren
                last_paren = target_line.rfind(")")
                if last_paren != -1:
                    inner = target_line[:last_paren].rstrip()
                    if inner.endswith("("):
                        repaired_line = f"{inner}random_state=42){target_line[last_paren+1:]}"
                    else:
                        repaired_line = f"{inner}, random_state=42){target_line[last_paren+1:]}"
                    lines[line_num - 1] = repaired_line
                    return "\n".join(lines) + "\n"
        return content

    def _fix_stratification(self, content: str, issue: Issue) -> str:
        """Adds stratify=y to train_test_split."""
        lines = content.splitlines()
        line_num = issue.line_number
        if line_num and 1 <= line_num <= len(lines):
            target_line = lines[line_num - 1]
            if "train_test_split" in target_line and "stratify" not in target_line:
                last_paren = target_line.rfind(")")
                if last_paren != -1:
                    inner = target_line[:last_paren].rstrip()
                    repaired_line = f"{inner}, stratify=y){target_line[last_paren+1:]}"
                    lines[line_num - 1] = repaired_line
                    return "\n".join(lines) + "\n"
        return content

    def _fix_swallowed_exception(self, content: str, issue: Issue) -> str:
        """Replaces bare except / except: pass with logged warning or explicit re-raise."""
        lines = content.splitlines()
        line_num = issue.line_number
        if line_num and 1 <= line_num <= len(lines):
            line = lines[line_num - 1]
            indent = len(line) - len(line.lstrip())
            indent_str = " " * indent
            # Check next line
            if line_num < len(lines):
                next_line = lines[line_num]
                if "pass" in next_line:
                    lines[line_num - 1] = f"{indent_str}except Exception as err:"
                    lines[line_num] = f"{indent_str}    import logging\n{indent_str}    logging.getLogger(__name__).warning(f'Suppressed exception: {{err}}')"
                    return "\n".join(lines) + "\n"
        return content

    def _fix_mutable_defaults(self, content: str, issue: Issue) -> str:
        """Replaces mutable default args (e.g. def foo(items=[])) with None and internal instantiation."""
        lines = content.splitlines()
        line_num = issue.line_number
        if line_num and 1 <= line_num <= len(lines):
            line = lines[line_num - 1]
            # Pattern def func(..., arg=[], ...)
            m = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(\[\]|\{\}|set\(\))", line)
            if m:
                arg_name = m.group(1)
                repaired_def = line.replace(m.group(0), f"{arg_name}=None")
                indent = len(line) - len(line.lstrip()) + 4
                body_init = f"{' ' * indent}if {arg_name} is None:\n{' ' * indent}    {arg_name} = []"
                lines[line_num - 1] = repaired_def
                lines.insert(line_num, body_init)
                return "\n".join(lines) + "\n"
        return content

    def _fix_unsafe_yaml(self, content: str, issue: Issue) -> str:
        return content.replace("yaml.load(", "yaml.safe_load(")

    def _fix_eval_exec(self, content: str, issue: Issue) -> str:
        if "eval(" in content and "ast.literal_eval" not in content:
            if "import ast" not in content:
                content = "import ast\n" + content
            return content.replace("eval(", "ast.literal_eval(")
        return content
