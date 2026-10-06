"""LLM reasoning layer for evidence-grounded repository repair.

The LLM is a bounded reasoning component: deterministic analyzers remain the
source of truth, while the model explains root causes and proposes candidate
repairs. Proposed changes are still validated by the existing patch validator.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, Field

from src.core.models import Issue


class RepairProposal(BaseModel):
    issue_id: str
    root_cause: str = ""
    rationale: str = ""
    replacement_code: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    safe_to_apply: bool = False


class LLMReasoningResult(BaseModel):
    enabled: bool = False
    model: str = ""
    proposals: list[RepairProposal] = Field(default_factory=list)
    error: str | None = None


def _load_env_file() -> None:
    """Lightweight .env loader without external dependencies."""
    for candidate in [".env", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")]:
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass


class LLMReasoningEngine:
    """Calls an OpenAI-compatible chat-completions endpoint.

    Supported providers include OpenAI-compatible gateways, Groq, and a local
    Ollama OpenAI-compatible endpoint. No provider SDK is required.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_sec: int = 45,
    ) -> None:
        _load_env_file()
        self.base_url = (
            base_url
            or os.getenv("REPO_DOCTOR_LLM_BASE_URL")
            or "http://localhost:11434/v1"
        ).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("REPO_DOCTOR_LLM_API_KEY", "")
        self.model = model or os.getenv("REPO_DOCTOR_LLM_MODEL", "qwen2.5-coder:7b")
        self.timeout_sec = timeout_sec

    @property
    def configured(self) -> bool:
        # Local Ollama does not require a key. Remote OpenAI-compatible
        # endpoints normally do.
        return self.base_url.startswith(("http://localhost:", "http://127.0.0.1:")) or bool(
            self.api_key
        )

    def reason(self, issues: list[Issue]) -> LLMReasoningResult:
        """Produce evidence-grounded root-cause and repair proposals."""
        if not issues:
            return LLMReasoningResult(enabled=False, model=self.model)

        if not self.configured:
            return LLMReasoningResult(
                enabled=False,
                model=self.model,
                error="LLM not configured; using deterministic repair rules.",
            )

        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are RepoDoctor's senior software-engineering reasoning engine. "
                        "Reason ONLY from supplied static-analysis evidence. Never invent files, "
                        "APIs, tests, or vulnerabilities. Return JSON with a 'proposals' array. "
                        "For each issue, explain root_cause and rationale. Only set safe_to_apply "
                        "true when a conservative replacement is directly supported by the "
                        "evidence. replacement_code must be the COMPLETE replacement content "
                        "for the affected file, not a diff. Prefer null when uncertain."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task": "Analyze these deterministic findings and propose conservative repairs.",
                            "issues": [issue.model_dump(mode="json") for issue in issues],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            parsed: dict[str, Any] = json.loads(content)
            proposals = [
                RepairProposal.model_validate(item)
                for item in parsed.get("proposals", [])
            ]
            allowed = {issue.id for issue in issues}
            proposals = [proposal for proposal in proposals if proposal.issue_id in allowed]
            return LLMReasoningResult(
                enabled=True,
                model=self.model,
                proposals=proposals,
            )
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
            return LLMReasoningResult(
                enabled=False,
                model=self.model,
                error=f"LLM reasoning unavailable: {exc}",
            )
        except Exception as exc:
            return LLMReasoningResult(
                enabled=False,
                model=self.model,
                error=f"LLM reasoning failed safely: {exc}",
            )
