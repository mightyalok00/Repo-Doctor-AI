"""
Tests for DockerSandboxRunner isolation and fallback.
"""

from src.sandbox.docker_runner import DockerSandboxRunner


def test_docker_runner_setup_and_cleanup():
    runner = DockerSandboxRunner(source_repo_path="examples/buggy_ml_repo")
    sandbox_path = runner.setup_sandbox()

    assert sandbox_path.exists()
    assert (sandbox_path / "model.py").exists()

    runner.cleanup()
    assert not sandbox_path.exists()


def test_docker_runner_test_execution_fallback():
    runner = DockerSandboxRunner(source_repo_path="examples/buggy_ml_repo")
    runner.setup_sandbox()

    res = runner.run_tests(timeout_sec=15)
    assert "passed" in res
    assert "failed" in res
    assert "runner" in res
    assert res["passed"] >= 0

    runner.cleanup()
