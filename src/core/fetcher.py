"""
RepoDoctor AI - Repository Fetcher and File Scanner
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class RepoFile:
    def __init__(self, relative_path: str, full_path: Path, content: str, is_python: bool = False):
        self.relative_path = relative_path
        self.full_path = full_path
        self.content = content
        self.is_python = is_python
        self.ast_tree: ast.AST | None = None
        self.lines: list[str] = content.splitlines()
        self.loc: int = len(self.lines)

        if is_python:
            try:
                self.ast_tree = ast.parse(content, filename=str(full_path))
            except Exception:
                self.ast_tree = None


class RepositoryFetcher:
    """Clones or loads a repository and prepares indexed files and AST trees."""

    IGNORE_DIRS = {
        ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
        ".mypy_cache", ".ruff_cache", "node_modules", "dist", "build",
        ".egg-info", ".tox", ".coverage", "site-packages"
    }

    IGNORE_EXTENSIONS = {
        ".pyc", ".pyd", ".pyo", ".so", ".dll", ".exe", ".bin",
        ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg",
        ".mp4", ".mp3", ".wav", ".zip", ".tar", ".gz", ".7z",
        ".pkl", ".joblib", ".h5", ".pt", ".pth", ".onnx", ".parquet", ".feather"
    }

    def __init__(self, target: str):
        """
        Target can be a local directory path or a GitHub repository URL
        (e.g., https://github.com/user/repo or git@github.com:user/repo.git)
        """
        self.target = target.strip()
        self.is_url = self.target.startswith("http://") or self.target.startswith("https://") or self.target.startswith("git@")
        self.temp_dir: str | None = None
        self.repo_path: Path = Path(".")
        self.repo_name: str = ""
        self.files: dict[str, RepoFile] = {}

    def fetch(self) -> Path:
        """Fetch/prepare the repository directory."""
        if self.is_url:
            self.temp_dir = tempfile.mkdtemp(prefix="repodoctor_")
            self.repo_name = self.target.rstrip("/").split("/")[-1].replace(".git", "")
            clone_target = Path(self.temp_dir) / self.repo_name
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", self.target, str(clone_target)],
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.repo_path = clone_target
            except Exception as e:
                # If git clone fails, raise clear exception
                raise RuntimeError(f"Failed to clone repository from {self.target}: {e!s}")
        else:
            local_path = Path(self.target).resolve()
            if not local_path.exists() or not local_path.is_dir():
                raise ValueError(f"Local path does not exist or is not a directory: {self.target}")
            self.repo_path = local_path
            self.repo_name = local_path.name

        self._scan_files()
        return self.repo_path

    def _scan_files(self) -> None:
        """Scan directory and index text/python files."""
        self.files.clear()
        for root, dirs, files in os.walk(self.repo_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                rel_path = os.path.relpath(file_path, self.repo_path).replace("\\", "/")

                # Skip binary / large model files
                if file_path.suffix.lower() in self.IGNORE_EXTENSIONS:
                    continue

                # Skip files larger than 2MB
                try:
                    if file_path.stat().st_size > 2 * 1024 * 1024:
                        continue
                except Exception:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    is_python = file.endswith(".py")
                    repo_file = RepoFile(
                        relative_path=rel_path,
                        full_path=file_path,
                        content=content,
                        is_python=is_python
                    )
                    self.files[rel_path] = repo_file
                except Exception:
                    continue

    def get_python_files(self) -> list[RepoFile]:
        return [f for f in self.files.values() if f.is_python]

    def get_file(self, rel_path: str) -> RepoFile | None:
        norm_path = rel_path.replace("\\", "/")
        return self.files.get(norm_path)

    def cleanup(self) -> None:
        """Clean up temporary directories if created."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
