# 🩺 RepoDoctor AI
> **An AI-powered autonomous engineer that diagnoses, scores, and repairs GitHub repositories.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.33+-FF4B4B.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Validated Repair](https://img.shields.io/badge/Sandbox-Self--Verifying-brightgreen)]()

---

## 🌟 The Core Idea
Give **RepoDoctor AI** any GitHub repository URL or local project path.

It automatically:
- 🔍 **Clones & Analyzes** the repository architecture and file hierarchy
- 🧠 **Diagnoses Anti-Patterns** across 8 core engineering dimensions
- 🧪 **Specialized ML Doctor™** detects data leakage, train-test contamination, unstratified splits, and missing seeds
- 🛡️ **Audits Dependencies & Security** (insecure deserialization, eval execution, unpinned versions)
- 🔧 **Generates Exact Unified Patches** for identified code and configuration bugs
- ⚙️ **Disposable Workspace Validation** runs real baseline and post-patch pytest executions in a disposable validation workspace before marking a patch verified
- 📈 **Repository Health Timeline** tracks continuous improvement across versions (e.g. `5.8 → 9.1`)
- 📑 **Generates Recruiter-Ready Engineering Reports** in Markdown and HTML formats

---

## 🏗️ System Architecture

```
                 GitHub / Local Repo
                         │
                         ▼
                 Repository Fetcher
                         │
                         ▼
             Static & AST Analyzers
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    Architecture      Security        Supply-Chain
      & Quality       & AST RCE       Dependencies
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 ML Doctor™ Engine
     (Leakage, Scaling, Stratification, Seeds)
                         │
                         ▼
                AI Reasoning Engine
             (Multi-Dimensional Scorecard)
                         │
                ┌────────┴────────┐
                ▼                 ▼
            Diagnosis          Patch
                                  │
                                  ▼
                         Sandbox Validator
                     (Pre-Test vs Post-Test)
                                  │
                                  ▼
                         Final Verified Report
```

---

## 📊 Multi-Dimensional Scorecard Rubric

RepoDoctor scores software projects across **8 weighted engineering dimensions**:
1. **Architecture** (Modularity, circular dependencies, God files, package namespace)
2. **Code Quality** (Cyclomatic complexity, swallowed exceptions, mutable defaults, type hints)
3. **Testing** (Pytest test presence, test-to-code ratio, assertion coverage)
4. **ML Engineering** (Data leakage, pre-split transforms, test contamination, pipelines)
5. **Security** (AST check for `eval`/`exec`, unsafe YAML load, hardcoded secrets)
6. **Documentation** (README quality, public docstring coverage, open-source licensing)
7. **Reproducibility** (Dependency pinning, lockfile presence, deterministic `random_state`)
8. **CI/CD & Deployment** (GitHub Actions workflows, Dockerfile best practices, `.gitignore`)

---

## 🧪 ML Doctor™ Specialization
RepoDoctor includes deep AST heuristic engines built for Scikit-Learn, PyTorch, LightGBM, and Pandas:

```python
# ⚠️ DATA LEAKAGE DETECTED (Before)
scaler = StandardScaler()
X = scaler.fit_transform(X) # ❌ Fitted on full dataset before splitting!
X_train, X_test, y_train, y_test = train_test_split(X, y)

# 🚀 REVISED AUTONOMOUS REPAIR (After)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42, stratify=y)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test) # ✅ Zero test-set contamination
```

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/your-username/repo-doctor-ai.git
cd repo-doctor-ai
pip install -e .
```

### Validation Safety Note\nRepoDoctor uses a disposable copy of the target repository for validation. This protects the source tree from test/patch mutations, but it is **not an OS-level security sandbox**. Do not execute untrusted repositories on a privileged host; use a container or VM for hostile code.\n\n### 2. Launch Streamlit Web Dashboard
```bash
streamlit run app/streamlit_app.py
```
Open `http://localhost:8501` to use the interactive dashboard with radar charts, 1-click repairs, and diff viewers.

### 3. Launch FastAPI REST Server
```bash
uvicorn app.api:app --reload --port 8000
```
Explore the interactive Swagger API documentation at `http://localhost:8000/docs`.

### 4. Terminal CLI Usage
```bash
# 1. Scan and score a repository
python -m src.cli scan examples/buggy_ml_repo

# 2. Diagnose, patch, and self-verify in sandbox
python -m src.cli fix examples/buggy_ml_repo

# 3. Apply verified fixes directly to disk
python -m src.cli fix examples/buggy_ml_repo --apply

# 4. Generate Recruiter-Ready Engineering Report
python -m src.cli report examples/buggy_ml_repo --output REPORT.md
```

---

## 📈 Health Timeline Tracking
Every time a repository is diagnosed or repaired, RepoDoctor persists historical snapshots:

```
Score
10 ┤                         ● (v4: 9.2)
 9 ┤                    ●────  (v3: 8.5)
 8 ┤              ●─────       (v2: 7.4)
 7 ┤        ●─────             (v1: 5.8 Initial Baseline)
 6 ┤  ●─────
 5 ┤
   └──────────────────────────
      v1    v2    v3    v4

"Your repository improved from 5.8 → 9.2 after 14 verified automated repairs."
```

---

## 🧪 Running Tests
```bash
pytest -v
```

---

## 📜 License
Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
