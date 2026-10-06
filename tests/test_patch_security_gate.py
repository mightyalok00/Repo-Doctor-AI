"""
Tests for Patch Security Gate and Safety Boundaries.
"""

from pathlib import Path
import pytest

from src.ai.patch_security_gate import PatchSecurityGate
from src.core.models import Patch


@pytest.fixture
def gate():
    return PatchSecurityGate(repo_root=Path.cwd())


def test_clean_patch_passes_security_gate(gate):
    clean_patch = Patch(
        issue_id="QUAL-001",
        file_path="src/model.py",
        description="Fix mutable default argument",
        original_code="def foo(items=[]):\n    pass\n",
        replacement_code="def foo(items=None):\n    if items is None:\n        items = []\n",
        diff="--- a/src/model.py\n+++ b/src/model.py\n",
    )
    decision = gate.evaluate(clean_patch)
    assert decision.passed is True
    assert len(decision.reasons) == 0


def test_reject_forbidden_imports(gate):
    malicious_patch = Patch(
        issue_id="SEC-001",
        file_path="src/utils.py",
        description="Injected socket reverse shell",
        original_code="def helper():\n    pass\n",
        replacement_code="import socket\ndef helper():\n    s = socket.socket()\n",
        diff="",
    )
    decision = gate.evaluate(malicious_patch)
    assert decision.passed is False
    assert any("socket" in r.lower() for r in decision.reasons)


def test_reject_dangerous_calls(gate):
    eval_patch = Patch(
        issue_id="SEC-002",
        file_path="src/calc.py",
        description="Re-introducing eval",
        original_code="def parse(x):\n    return int(x)\n",
        replacement_code="def parse(x):\n    return eval(x)\n",
        diff="",
    )
    decision = gate.evaluate(eval_patch)
    assert decision.passed is False
    assert any("eval" in r.lower() for r in decision.reasons)


def test_reject_os_system_call(gate):
    system_patch = Patch(
        issue_id="SEC-003",
        file_path="src/script.py",
        description="Call os.system",
        original_code="import os\ndef run():\n    pass\n",
        replacement_code="import os\ndef run():\n    os.system('rm -rf /')\n",
        diff="",
    )
    decision = gate.evaluate(system_patch)
    assert decision.passed is False
    assert any("os.system" in r.lower() for r in decision.reasons)


def test_reject_path_traversal(gate):
    traversal_patch = Patch(
        issue_id="SEC-004",
        file_path="../../etc/passwd",
        description="Escape repo root",
        original_code="",
        replacement_code="root:x:0:0:root:/root:/bin/bash\n",
        diff="",
    )
    decision = gate.evaluate(traversal_patch)
    assert decision.passed is False
    assert any("traversal" in r.lower() or "escapes" in r.lower() for r in decision.reasons)


def test_reject_oversized_diff_hallucination(gate):
    # 15 lines original, but 100 lines hallucinated replacement
    orig = "\n".join([f"line_{i} = {i}" for i in range(15)])
    replacement = "\n".join([f"line_{i} = {i}" for i in range(100)])
    bloat_patch = Patch(
        issue_id="QUAL-002",
        file_path="src/bloat.py",
        description="Massive hallucination",
        original_code=orig,
        replacement_code=replacement,
        diff="",
    )
    decision = gate.evaluate(bloat_patch)
    assert decision.passed is False
    assert any("expands" in r.lower() for r in decision.reasons)
