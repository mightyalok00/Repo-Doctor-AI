"""Self-verifying patch validation in isolated temporary workspaces."""

from __future__ import annotations

from pathlib import Path

from src.core.git_utils import apply_patch_to_file
from src.core.models import Patch, ValidationResult, ValidationStatus, ValidationStep
from src.sandbox.runner import SandboxRunner


class PatchValidator:
    """Validate patches with real pre/post test executions.

    Validation is performed in disposable copies of the repository. This is
    an isolated workspace, not a security boundary; untrusted code should be
    evaluated in a container or VM.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path.resolve()

    def validate_patch(self, patch: Patch) -> ValidationResult:
        results = self.validate_all_patches([patch])
        return results[0]

    def validate_all_patches(self, patches: list[Patch]) -> list[ValidationResult]:
        """Run genuine before/after tests for every candidate patch."""
        if not patches:
            return []

        results: list[ValidationResult] = []

        for patch in patches:
            runner = SandboxRunner(self.repo_path)
            try:
                sandbox_dir = runner.setup_sandbox()

                baseline = runner.run_tests(timeout_sec=30)
                steps = [
                    ValidationStep(
                        name="Baseline Test Execution",
                        status=(
                            ValidationStatus.PASSED
                            if baseline["success"]
                            else ValidationStatus.WARNING
                        ),
                        details=(
                            f'Pre-patch baseline: {baseline["passed"]} passed, '
                            f'{baseline["failed"]} failed, {baseline["errors"]} errors'
                        ),
                    )
                ]

                target_file = sandbox_dir / patch.file_path
                applied = apply_patch_to_file(
                    target_file, patch.replacement_code
                )
                steps.append(
                    ValidationStep(
                        name="Patch Application",
                        status=(
                            ValidationStatus.PASSED
                            if applied
                            else ValidationStatus.FAILED
                        ),
                        details=(
                            f"Applied patch to '{patch.file_path}'"
                            if applied
                            else f"Failed to apply patch to '{patch.file_path}'"
                        ),
                    )
                )

                if not applied:
                    results.append(
                        ValidationResult(
                            patch_id=patch.issue_id,
                            file_path=patch.file_path,
                            overall_status=ValidationStatus.FAILED,
                            steps=steps,
                            confidence=0.0,
                        )
                    )
                    continue

                syntax_ok = True
                syntax_msg = "Non-Python file; syntax check skipped."
                if patch.file_path.endswith(".py"):
                    try:
                        compile(
                            patch.replacement_code,
                            str(target_file),
                            "exec",
                        )
                        syntax_msg = "Python syntax verified."
                    except SyntaxError as exc:
                        syntax_ok = False
                        syntax_msg = (
                            f"Syntax error: {exc.msg} at line {exc.lineno}"
                        )

                steps.append(
                    ValidationStep(
                        name="Syntax Verification",
                        status=(
                            ValidationStatus.PASSED
                            if syntax_ok
                            else ValidationStatus.FAILED
                        ),
                        details=syntax_msg,
                    )
                )

                post = (
                    runner.run_tests(timeout_sec=30)
                    if syntax_ok
                    else {
                        "passed": 0,
                        "failed": 1,
                        "errors": 1,
                        "output": syntax_msg,
                        "success": False,
                    }
                )
                tests_passed = (
                    post["success"]
                    and post["failed"] == 0
                    and post["errors"] == 0
                )
                steps.append(
                    ValidationStep(
                        name="Post-Patch Test Execution",
                        status=(
                            ValidationStatus.PASSED
                            if tests_passed
                            else ValidationStatus.FAILED
                        ),
                        details=(
                            f'Post-patch: {post["passed"]} passed, '
                            f'{post["failed"]} failed, {post["errors"]} errors'
                        ),
                    )
                )

                verified = syntax_ok and tests_passed
                results.append(
                    ValidationResult(
                        patch_id=patch.issue_id,
                        file_path=patch.file_path,
                        overall_status=(
                            ValidationStatus.PASSED
                            if verified
                            else ValidationStatus.FAILED
                        ),
                        syntax_check=syntax_ok,
                        import_check=tests_passed,
                        tests_passed_before=baseline["passed"],
                        tests_failed_before=baseline["failed"],
                        tests_passed_after=post["passed"],
                        tests_failed_after=post["failed"],
                        test_output=post["output"],
                        steps=steps,
                        confidence=0.99 if verified else 0.20,
                    )
                )
            finally:
                runner.cleanup()

        return results
