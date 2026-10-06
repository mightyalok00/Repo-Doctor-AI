"""
RepoDoctor AI - Git Utilities and Diff Management
"""

from __future__ import annotations

import difflib
import subprocess
from pathlib import Path


def generate_diff(original_text: str, new_text: str, file_path: str = "") -> str:
    """Generate a clean unified diff between original and updated text."""
    orig_lines = original_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        new_lines,
        fromfile=f"a/{file_path}" if file_path else "original",
        tofile=f"b/{file_path}" if file_path else "repaired",
        lineterm=""
    )
    return "".join(diff)


def apply_patch_to_file(file_path: Path, new_content: str) -> bool:
    """Safely apply updated content to a file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception:
        return False


def get_git_info(repo_path: Path) -> dict:
    """Extract git commit/branch metadata if available."""
    info = {
        "is_git_repo": False,
        "branch": "unknown",
        "commit_hash": "unknown",
        "author": "unknown"
    }
    if not (repo_path / ".git").exists():
        return info

    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        info["is_git_repo"] = True
        info["branch"] = branch or "main"
        info["commit_hash"] = commit or "latest"
    except Exception:
        pass

    return info
