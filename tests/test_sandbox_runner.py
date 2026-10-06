"""Tests for disposable validation behavior."""

from pathlib import Path

from src.sandbox.runner import SandboxRunner


def test_runner_executes_real_tests_and_keeps_source_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    test_file = source / "test_sample.py"
    test_file.write_text(
        "def test_truth():\n"
        "    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )

    runner = SandboxRunner(source)
    try:
        runner.setup_sandbox()
        result = runner.run_tests(timeout_sec=30)
    finally:
        runner.cleanup()

    assert result["success"] is True
    assert result["passed"] == 1
    assert test_file.read_text(encoding="utf-8") == (
        "def test_truth():\n"
        "    assert 1 + 1 == 2\n"
    )


def test_runner_reports_test_failures(tmp_path: Path) -> None:
    source = tmp_path / "repo"
    source.mkdir()
    (source / "test_failure.py").write_text(
        "def test_failure():\n"
        "    assert False\n",
        encoding="utf-8",
    )

    runner = SandboxRunner(source)
    try:
        runner.setup_sandbox()
        result = runner.run_tests(timeout_sec=30)
    finally:
        runner.cleanup()

    assert result["success"] is False
    assert result["failed"] == 1
