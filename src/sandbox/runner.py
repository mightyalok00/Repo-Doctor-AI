"""Execute repository tests in disposable validation workspaces."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class SandboxRunner:
    """Manage a disposable workspace used for deterministic verification.

    The workspace prevents file changes from reaching the source repository.
    It is intentionally not described as a security sandbox because arbitrary
    repository code can still execute with the host user's privileges.
    """

    IGNORE_NAMES = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        "build",
    }

    def __init__(self, source_repo_path: Path):
        self.source_repo_path = source_repo_path.resolve()
        self.sandbox_dir: Path | None = None

    def setup_sandbox(self) -> Path:
        """Create a fresh temporary copy of the repository."""
        temp_dir = tempfile.mkdtemp(prefix="repodoctor_validation_")
        self.sandbox_dir = Path(temp_dir)

        def ignore_patterns(_path: str, names: list[str]) -> set[str]:
            return {name for name in names if name in self.IGNORE_NAMES}

        shutil.copytree(
            self.source_repo_path,
            self.sandbox_dir,
            dirs_exist_ok=True,
            ignore=ignore_patterns,
        )
        return self.sandbox_dir

    def run_syntax_check(self) -> tuple[bool, str]:
        if not self.sandbox_dir:
            return False, "Validation workspace not initialized."

        errors: list[str] = []
        for py_file in self.sandbox_dir.rglob("*.py"):
            try:
                content = py_file.read_text(
                    encoding="utf-8", errors="replace"
                )
                compile(content, str(py_file), "exec")
            except SyntaxError as exc:
                errors.append(
                    f"{py_file.name}:{exc.lineno} - {exc.msg}"
                )
            except OSError as exc:
                errors.append(f"{py_file.name} - {exc}")

        return (
            (False, "\n".join(errors))
            if errors
            else (True, "All Python files compiled successfully.")
        )

    def run_tests(self, timeout_sec: int = 30) -> dict[str, Any]:
        """Run pytest with a sanitized environment and hard timeout."""
        if not self.sandbox_dir:
            return self._failure("Validation workspace not initialized.")

        test_files = list(self.sandbox_dir.rglob("test_*.py"))
        test_files += list(self.sandbox_dir.rglob("*_test.py"))
        if not test_files:
            return {
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "output": "No pytest test files found.",
                "success": True,
            }

        cmd = [
            sys.executable,
            "-I",
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "--no-header",
        ]

        # Prevent user-site packages and inherited secrets from influencing tests.
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USERPROFILE": os.environ.get("USERPROFILE", ""),
            "TEMP": os.environ.get("TEMP", tempfile.gettempdir()),
            "TMP": os.environ.get("TMP", tempfile.gettempdir()),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
        }

        try:
            completed = subprocess.run(
                cmd,
                cwd=self.sandbox_dir,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._failure(
                f"Test execution timed out after {timeout_sec} seconds."
            )
        except OSError as exc:
            return self._failure(f"Failed to execute pytest: {exc}")

        output = f"{completed.stdout}\n{completed.stderr}".strip()
        passed = self._extract_count(output, r"(\d+)\s+passed")
        failed = self._extract_count(output, r"(\d+)\s+failed")
        errors = self._extract_count(output, r"(\d+)\s+error")

        success = completed.returncode == 0 and failed == 0 and errors == 0
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": output,
            "success": success,
        }

    @staticmethod
    def _extract_count(text: str, pattern: str) -> int:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _failure(message: str) -> dict[str, Any]:
        return {
            "passed": 0,
            "failed": 1,
            "errors": 1,
            "output": message,
            "success": False,
        }

    def cleanup(self) -> None:
        if self.sandbox_dir and self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir, ignore_errors=True)
            self.sandbox_dir = None
