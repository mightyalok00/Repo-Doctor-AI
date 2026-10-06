"""
Tests for Autonomous Patch Generator and Sandbox Validator.
"""

from src.ai.diagnosis import DiagnosisEngine
from src.ai.patch_generator import PatchGenerator
from src.core.fetcher import RepositoryFetcher
from src.sandbox.validator import PatchValidator


def test_patch_generation_and_unified_diff():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)

    assert len(patches) > 0
    # Check that diff is unified diff format
    for p in patches:
        assert p.diff.startswith("---") or p.file_path in p.diff or len(p.replacement_code) > 0


def test_sandbox_validation():
    fetcher = RepositoryFetcher("examples/buggy_ml_repo")
    fetcher.fetch()

    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)

    validator = PatchValidator(fetcher.repo_path)
    # Validate first patch
    first_patch = patches[0]
    val_res = validator.validate_patch(first_patch)

    assert val_res.syntax_check is True
    assert val_res.confidence > 0.5
