# 🩺 Repo-Doctor-AI — Project Documentation

## 1. Overview

Repo-Doctor-AI is an AI-powered software engineering tool that works like a **doctor for code repositories**. It analyzes a project, identifies problems, uses AI to understand root causes, generates possible fixes, checks those fixes for security, runs tests, and verifies whether the repair actually works.

**Core idea:** Detect → Understand → Fix → Secure → Test → Verify

## 2. Problem Statement

Software repositories can contain:
- Bugs and code-quality problems
- Security vulnerabilities
- Machine-learning mistakes
- Dependency issues
- Missing or weak tests
- Poor project structure
- CI/CD problems
- Documentation and reproducibility issues

Repo-Doctor-AI automates much of this diagnosis and repair workflow.

## 3. System Architecture

```
Repository
    ↓
Static / AST Analysis
    ↓
Problem Detection
    ↓
ML Diagnosis
    ↓
LLM Reasoning
    ↓
Patch Generation
    ↓
Security Validation
    ↓
Docker Sandbox
    ↓
Real Tests
    ↓
Verified Result & Report
```

The LLM is not treated as an unrestricted code editor. It receives evidence from repository analysis, proposes a repair, and the proposed repair passes validation and testing before it is considered successful.

## 4. Installation

### Requirements

- Python 3.10+
- Git
- Docker (recommended for sandbox validation)
- Ollama (optional, for local LLM usage)

### Clone

```bash
git clone https://github.com/mightyalok00/Repo-Doctor-AI.git
cd Repo-Doctor-AI
```

### Virtual Environment

**Windows**
```bash
python -m venv .venv
.venv\\Scripts\\activate
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install

```bash
pip install -e .
```

### Verify

```bash
python -m src.cli --help
```

## 5. LLM Configuration

Repo-Doctor-AI supports local Ollama and OpenRouter-compatible APIs.

### Local Ollama

```bash
ollama pull qwen2.5-coder:7b
```

Default endpoint:

```
http://localhost:11434/v1
```

Default model:

```
qwen2.5-coder:7b
```

### OpenRouter

Create a `.env` file:

```env
REPO_DOCTOR_LLM_BASE_URL=https://openrouter.ai/api/v1
REPO_DOCTOR_LLM_API_KEY=your_api_key
REPO_DOCTOR_LLM_MODEL=your_provider/model-name
```

## 6. Usage

### Scan

```bash
python -m src.cli scan examples/buggy_ml_repo
```

### Repair

```bash
python -m src.cli fix examples/buggy_ml_repo
```

The repair workflow can analyze the repository, find issues, use the LLM for eligible issues, generate proposed fixes, validate patches, run security checks, and test the changes.

### Specify an LLM Model

```bash
python -m src.cli fix examples/buggy_ml_repo --llm-model qwen2.5-coder:7b
```

### Generate Report

```bash
python -m src.cli report examples/buggy_ml_repo --output REPO_DOCTOR_REPORT.md
```

## 7. Dashboard & API

### Streamlit

```bash
streamlit run app/streamlit_app.py
```

The dashboard provides visual views of repository health, detected issues, AI reasoning, generated fixes, security results, tests, and scores.

### FastAPI

```bash
uvicorn app.api:app --reload
```

## 8. Repair Workflow

1. **Repository Analysis** — examines project structure, source code, dependencies, tests, and configuration.
2. **Problem Detection** — uses static and AST-based analysis.
3. **AI Reasoning** — the LLM determines the root cause and possible solution from evidence.
4. **Patch Generation** — uses deterministic fixes and/or LLM-generated patches.
5. **Security Validation** — Patch Security Gate checks for newly introduced risks.
6. **Safe Testing** — proposed repairs can be tested in Docker.
7. **Verification** — tests are compared before and after the repair.

```
Before Fix → Run Tests
      ↓
Apply Patch
      ↓
After Fix → Run Tests
      ↓
Compare Results
      ↓
Verified Repair
```

## 9. Security

The system can identify or validate risks including:
- Dangerous code execution
- Unsafe YAML loading
- Hardcoded secrets
- Shell execution risks
- SQL injection patterns
- Vulnerabilities introduced by proposed patches

The patch security layer helps ensure that an AI-generated fix does not create a new problem while solving the original one.

## 10. Testing & CI/CD

GitHub Actions includes:
- Ruff linting
- Python compatibility testing
- Pytest
- Repository self-audit
- CLI verification
- Docker build verification

The CI test matrix covers Python 3.10, 3.11, 3.12, and 3.13.

## 11. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| AST / Static Analysis | Code inspection |
| Scikit-learn | ML analysis / diagnostics |
| Qwen 2.5 Coder / OpenRouter | AI reasoning |
| FastAPI | REST API |
| Streamlit | Dashboard |
| Pytest | Testing |
| Ruff | Linting |
| Docker | Controlled testing |
| GitHub Actions | CI/CD |

## 12. Main Features

- 🔍 Repository Diagnosis
- 🧠 AI Root-Cause Analysis
- 🔧 Automated Repair
- 🛡️ Patch Security Gate
- 🐳 Docker Validation
- 🧪 Real Test Verification
- 📊 Repository Scorecard
- 🚀 CI/CD

## 13. Portfolio Value

The project demonstrates practical knowledge of:

**AI/LLMs + Python + Machine Learning + Static Analysis + Software Engineering + Security + Docker + Testing + CI/CD**

It demonstrates an end-to-end AI software-engineering workflow rather than only an AI chatbot.

## 14. Professional Assessment

**Overall Portfolio Rating: 9.5/10**

| Area | Score |
|---|---:|
| Architecture | 9.5/10 |
| AI / LLM Engineering | 9.5/10 |
| ML Engineering | 9.0/10 |
| Security | 9.5/10 |
| Testing | 9.4/10 |
| CI/CD | 9.5/10 |
| UI/UX | 9.3/10 |
| Portfolio Value | 9.7/10 |

## 15. Simple Explanation for a Mentor

> “Repo-Doctor-AI is like a doctor for software projects. It checks a repository, finds problems, uses AI to understand the root cause, suggests a fix, checks the fix for security, tests it in a controlled environment, and verifies whether the fix actually works.”

## 16. Future Improvements

- Stronger restrictions on files an LLM can modify
- Maximum patch and diff-size limits
- More advanced Docker isolation
- Resource and network restrictions
- More end-to-end tests
- Expanded ML diagnosis models
- Improved patch verification
- Support for additional programming languages

## 17. Conclusion

Repo-Doctor-AI combines traditional software engineering techniques with modern AI to create an automated repository diagnosis and repair system.

**Core principle:** Don't just generate a fix — verify that the fix is safe and actually works.
