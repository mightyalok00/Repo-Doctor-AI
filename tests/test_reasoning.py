"""Tests for the bounded LLM reasoning layer."""

from src.ai.reasoning import LLMReasoningEngine


def test_reasoning_falls_back_without_remote_configuration() -> None:
    engine = LLMReasoningEngine(
        base_url="https://example.invalid/v1",
        api_key="",
        model="test-model",
    )

    result = engine.reason([])

    assert result.enabled is False
    assert result.proposals == []


def test_local_ollama_endpoint_does_not_require_api_key() -> None:
    engine = LLMReasoningEngine(
        base_url="http://localhost:11434/v1",
        api_key="",
    )

    assert engine.configured is True
