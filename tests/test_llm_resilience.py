"""
Tests for LLM Reasoning Engine resilience and response parsing.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from src.ai.reasoning import LLMReasoningEngine
from src.core.models import Category, Issue, Severity


@pytest.fixture
def sample_issue():
    return Issue(
        id="QUAL-001",
        category=Category.CODE_QUALITY,
        title="Mutable Default Argument",
        severity=Severity.MEDIUM,
        file_path="src/model.py",
        line_number=10,
        risk_explanation="Shared state across calls",
        recommendation="Use None as default",
        auto_fixable=True,
    )


def test_llm_unconfigured_fallback(sample_issue):
    engine = LLMReasoningEngine(base_url="http://remote.invalid/v1", api_key="")
    res = engine.reason([sample_issue])
    assert res.enabled is False
    assert "not configured" in (res.error or "").lower()


def test_llm_clean_response_parsing(sample_issue):
    engine = LLMReasoningEngine(base_url="http://localhost:11434/v1")

    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "proposals": [
                            {
                                "issue_id": "QUAL-001",
                                "root_cause": "Default arg instantiated once",
                                "rationale": "Use None guard",
                                "safe_to_apply": True,
                                "confidence": 0.95
                            }
                        ]
                    })
                }
            }
        ]
    }

    with patch("urllib.request.urlopen") as mock_url:
        mock_cm = MagicMock()
        mock_cm.read.return_value = json.dumps(mock_response).encode("utf-8")
        mock_url.return_value.__enter__.return_value = mock_cm

        res = engine.reason([sample_issue])
        assert len(res.proposals) == 1
        assert res.proposals[0].issue_id == "QUAL-001"
        assert res.proposals[0].safe_to_apply is True


def test_llm_filters_hallucinated_issue_ids(sample_issue):
    engine = LLMReasoningEngine(base_url="http://localhost:11434/v1")

    # LLM returns proposal for issue id not in request
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "proposals": [
                            {
                                "issue_id": "FAKE-ID-9999",
                                "root_cause": "Invented issue",
                                "rationale": "Fake",
                                "safe_to_apply": True,
                            }
                        ]
                    })
                }
            }
        ]
    }

    with patch("urllib.request.urlopen") as mock_url:
        mock_cm = MagicMock()
        mock_cm.read.return_value = json.dumps(mock_response).encode("utf-8")
        mock_url.return_value.__enter__.return_value = mock_cm

        res = engine.reason([sample_issue])
        assert len(res.proposals) == 0  # Filtered out fake ID
