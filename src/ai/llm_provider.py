"""
RepoDoctor AI - LLM Provider and AI Reasoning Bridge
Supports local Ollama, OpenAI/Groq APIs, and deterministic AST rule synthesizer.
"""

from __future__ import annotations

import os

import httpx


class LLMProvider:
    """Provides access to LLM reasoning endpoints (Ollama, Groq, OpenAI) with graceful fallbacks."""

    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "llama3:8b")

    def is_llm_available(self) -> bool:
        """Check if any LLM backend is configured or reachable."""
        if self.openai_api_key or self.groq_api_key:
            return True
        try:
            resp = httpx.get(f"{self.ollama_host}/api/tags", timeout=1.0)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_explanation(self, title: str, code_snippet: str, context: str) -> str:
        """Generate contextual explanation for a detected issue."""
        if not self.is_llm_available():
            return f"Heuristic Analysis: {title}. Code pattern requires refactoring to comply with robust engineering standards."

        prompt = f"""You are RepoDoctor AI, an elite software diagnostic engineer.
Explain the root cause and engineering risk of this code finding concisely in 2 sentences.

Issue: {title}
Context: {context}
Code:
```python
{code_snippet}
```
"""
        try:
            if self.openai_api_key:
                headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
                resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                payload = {"model": self.model_name, "prompt": prompt, "stream": False}
                resp = httpx.post(f"{self.ollama_host}/api/generate", json=payload, timeout=8.0)
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception:
            pass

        return f"Deterministic finding: {title}."
