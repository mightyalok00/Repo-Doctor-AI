"""
RepoDoctor AI - Isolated Sandbox Runner
Executes tests, syntax validation, and import checks inside temporary isolated environments.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class SandboxRunner:
    """Manages an isolated copy of a repository for safe verification."""

    def __init__(self, source_repo_path: Path):
        self.source_repo_path = source_repo_path.resolve()
        self.sandbox_dir: Path | None = None

    def setup_sandbox(self) -> Path:
        """Create a fresh temporary sandbox copy of the repository."""
        temp_dir = tempfile.mkdtemp(prefix="repodoctor_sb_")
        self.sandbox_dir = Path(temp_dir)
        
        # Copy source files (excluding .git, venv, cache)
        def ignore_patterns(path, names):
            return {n for n in names if n in {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}}

        shutil.copytree(self.source_repo_path, self.sandbox_dir, dirs_exist_ok=True, ignore=ignore_patterns)
        return self.sandbox_dir

    def run_syntax_check(self) -> tuple[bool, str]:
        """Verify Python syntax across all .py files in sandbox."""
        if not self.sandbox_dir:
            return False, "Sandbox not initialized"

        errors = []
        for py_file in self.sandbox_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                compile(content, str(py_file), "exec")
            except SyntaxError as e:
                errors.append(f"{py_file.name}:{e.lineno} - {e.msg}")
            except Exception as e:
                errors.append(f"{py_file.name} - {e!s}")

        if errors:
            return False, "\n".join(errors)
        return True, "All Python files compiled successfully."

    def run_tests(self, timeout_sec: int = 10) -> dict[str, Any]:
        """Execute pytest in the sandbox environment and parse results."""
        if not self.sandbox_dir:
            return {"passed": 0, "failed": 0, "errors": 0, "output": "Sandbox not initialized", "success": False}

        # Check if tests exist
        test_files = list(self.sandbox_dir.rglob("test_*.py")) + list(self.sandbox_dir.rglob("*_test.py"))
        if not test_files:
            return {
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "output": "No pytest test files found in repository.",
                "success": True
            }

        cmd = [sys.executable, "-m", "pytest", "-q", "--disable-warnings", "--no-header"]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.sandbox_dir) + os.pathsep + env.get("PYTHONPATH", "")

        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.sandbox_dir),
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                env=env
            )
            stdout = res.stdout
            stderr = res.stderr
            full_out = f"{stdout}\n{stderr}".strip()

            passed = 0
            failed = 0
            errors = 0

            import re
            m_pass = re.search(r"(\d+)\s+passed", full_out)
            if m_pass:
                passed = int(m_pass.group(1))

            m_fail = re.search(r"(\d+)\s+failed", full_out)
            if m_fail:
                failed = int(m_fail.group(1))

            m_err = re.search(r"(\d+)\s+error", full_out)
            if m_err:
                errors = int(m_err.group(1))

            # If quiet output like "3 passed in 0.05s"
            if passed == 0 and failed == 0 and errors == 0 and res.returncode == 0:
                if "passed" in full_out:
                    passed = 1

            success = (res.returncode == 0) and (failed == 0) and (errors == 0)
            return {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "output": full_out,
                "success": success
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": 0,
                "failed": 1,
                "errors": 1,
                "output": f"Test execution timed out after {timeout_sec} seconds.",
                "success": False
            }
        except Exception as e:
            return {
                "passed": 0,
                "failed": 1,
                "errors": 1,
                "output": f"Failed to execute pytest: {e!s}",
                "success": False
            }

    def cleanup(self):
        """Remove temporary sandbox directory."""
        if self.sandbox_dir and self.sandbox_dir.exists():
            try:
                shutil.rmtree(self.sandbox_dir, ignore_errors=True)
            except Exception:
                pass
