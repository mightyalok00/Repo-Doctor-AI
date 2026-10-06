# 🩺 RepoDoctor AI - Engineering Health Report
**Repository:** `buggy_ml_repo` | **Date:** 2026-10-06 07:53:47 UTC
**Overall Health Score:** `7.1 / 10.0` (Grade: **B**)

---

## 📊 Executive Summary
Repository scored **7.1/10** (Grade: **B**) across 8 engineering dimensions. Found **21 total issues** (3 Critical, 4 High, 9 Medium). 🚨 **Critical Attention Required**: Arbitrary Code Execution via 'eval()' in `model.py`.

## 🏆 Repository Scorecard
| Category | Score / 10 | Issues Found | Critical | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Architecture** | **10.0** | 0 | 0 | 🟢 Excellent health |
| **Code Quality** | **7.7** | 2 | 0 | 🟡 Minor issues found |
| **Testing** | **10.0** | 0 | 0 | 🟢 Excellent health |
| **ML Engineering** | **2.8** | 6 | 2 | 🔴 Needs immediate attention |
| **Security** | **7.5** | 1 | 1 | 🟡 Minor issues found |
| **Documentation** | **8.6** | 3 | 0 | 🟢 Minor issues found |
| **Reproducibility** | **4.5** | 6 | 0 | 🔴 Needs immediate attention |
| **CI/CD** | **6.7** | 3 | 0 | 🟡 Needs immediate attention |
| **OVERALL** | **`7.1`** | **21** | **3** | **Grade: B** |

## 🚨 Critical & High Priority Findings
### 1. ⚠️ [HIGH] Silent Exception Swallowing (except: pass)
- **Location:** `model.py` (Line: 19)
- **Confidence:** `98%` | **Category:** `Code Quality`
- **Risk Analysis:** Silently swallowing exceptions hides critical runtime bugs, unexpected data corruptions, and breaks debuggability.
```python
    except:
        # ANTI-PATTERN: Swallowed exception
        pass
```
- **Recommended Fix:** Catch specific exception types and log errors appropriately using a logger (e.g., logger.warning or logger.exception).

### 2. ⚠️ [HIGH] Deprecated/Insecure Dependency 'sklearn'
- **Location:** `requirements.txt` (Line: 3)
- **Confidence:** `99%` | **Category:** `Reproducibility`
- **Risk Analysis:** Package 'sklearn' is deprecated on PyPI. Install 'scikit-learn' instead.
```python
sklearn
```
- **Recommended Fix:** Replace 'sklearn' with 'scikit-learn'.

### 3. 🔥 [CRITICAL] Arbitrary Code Execution via 'eval()'
- **Location:** `model.py` (Line: 10)
- **Confidence:** `99%` | **Category:** `Security`
- **Risk Analysis:** Using 'eval()' evaluates arbitrary string input as Python code, creating severe remote code execution (RCE) vulnerabilities.
```python
return eval(param_str)
```
- **Recommended Fix:** Refactor to avoid 'eval()'. Use `ast.literal_eval()` for safe literal parsing or structured data parsing (json).

### 4. ⚠️ [HIGH] Missing Automated CI/CD Workflows
- **Location:** `.github/workflows/ci.yml` (Line: 1)
- **Confidence:** `98%` | **Category:** `CI/CD`
- **Risk Analysis:** Repository lacks automated Continuous Integration (CI) workflows. Commits and Pull Requests are not automatically tested or linted before merging.
- **Recommended Fix:** Add a GitHub Actions workflow `.github/workflows/ci.yml` running pytest, ruff linting, and type checks on every push and pull request.

### 5. ⚠️ [HIGH] Missing .gitignore File
- **Location:** `.gitignore` (Line: 1)
- **Confidence:** `99%` | **Category:** `CI/CD`
- **Risk Analysis:** Repository lacks a .gitignore file, risking accidental commits of virtual environments, cache files, and sensitive .env files.
- **Recommended Fix:** Add a standard Python .gitignore ignoring `.env`, `__pycache__`, `.venv`, and temporary artifacts.

### 6. 🔥 [CRITICAL] Data Leakage: Preprocessing Fitted Before train_test_split()
- **Location:** `data_pipeline.py` (Line: 21)
- **Confidence:** `98%` | **Category:** `ML Engineering`
- **Risk Analysis:** Transformer (scaler/imputer/encoder) is fitted on the entire dataset prior to splitting. Test set statistics (mean, variance, category frequencies) contaminate the training preprocessing pipeline, causing artificially inflated evaluation metrics and real-world performance degradation.
```python
X = scaler.fit_transform(X)
...
X_train, X_test, y_train, y_test = train_test_split(X, y)
```
- **Recommended Fix:** Fit transformers ONLY on training data (`scaler.fit(X_train)` or wrap in `sklearn.pipeline.Pipeline`). Use `.transform(X_test)` on test data.

### 7. 🔥 [CRITICAL] Data Leakage: Preprocessing Fitted Before train_test_split()
- **Location:** `data_pipeline.py` (Line: 21)
- **Confidence:** `98%` | **Category:** `ML Engineering`
- **Risk Analysis:** Transformer (scaler/imputer/encoder) is fitted on the entire dataset prior to splitting. Test set statistics (mean, variance, category frequencies) contaminate the training preprocessing pipeline, causing artificially inflated evaluation metrics and real-world performance degradation.
```python
X = scaler.fit_transform(X)
...
X_train, X_test, y_train, y_test = train_test_split(X, y)
```
- **Recommended Fix:** Fit transformers ONLY on training data (`scaler.fit(X_train)` or wrap in `sklearn.pipeline.Pipeline`). Use `.transform(X_test)` on test data.

## 🧪 ML Doctor™ Diagnostics
Specialized machine learning integrity analysis:
- **Data Leakage: Preprocessing Fitted Before train_test_split()** (`data_pipeline.py`)
  - *Problem:* Transformer (scaler/imputer/encoder) is fitted on the entire dataset prior to splitting. Test set statistics (mean, variance, category frequencies) contaminate the training preprocessing pipeline, causing artificially inflated evaluation metrics and real-world performance degradation.
  - *Fix:* Fit transformers ONLY on training data (`scaler.fit(X_train)` or wrap in `sklearn.pipeline.Pipeline`). Use `.transform(X_test)` on test data.
- **Data Leakage: Preprocessing Fitted Before train_test_split()** (`data_pipeline.py`)
  - *Problem:* Transformer (scaler/imputer/encoder) is fitted on the entire dataset prior to splitting. Test set statistics (mean, variance, category frequencies) contaminate the training preprocessing pipeline, causing artificially inflated evaluation metrics and real-world performance degradation.
  - *Fix:* Fit transformers ONLY on training data (`scaler.fit(X_train)` or wrap in `sklearn.pipeline.Pipeline`). Use `.transform(X_test)` on test data.
- **Missing Scikit-Learn Pipeline Encapsulation** (`data_pipeline.py`)
  - *Problem:* Manual transformer chaining (`scaler.fit_transform(...)` + `model.fit(...)`) leads to fragmented preprocessing, test-time inconsistency, and errors during inference serving.
  - *Fix:* Encapsulate preprocessing and estimator in an `sklearn.pipeline.Pipeline` or `make_pipeline(StandardScaler(), Model())`.
- **Missing 'random_state' in 'train_test_split()'** (`data_pipeline.py`)
  - *Problem:* Invoking `train_test_split()` without a deterministic `random_state` causes non-reproducible splits/model weights across training runs, preventing experiment reproducibility.
  - *Fix:* Pass an explicit random state, e.g. `train_test_split(..., random_state=42)`.
- **Missing 'random_state' in 'RandomForestClassifier()'** (`data_pipeline.py`)
  - *Problem:* Invoking `RandomForestClassifier()` without a deterministic `random_state` causes non-reproducible splits/model weights across training runs, preventing experiment reproducibility.
  - *Fix:* Pass an explicit random state, e.g. `RandomForestClassifier(..., random_state=42)`.
- **Absence of K-Fold Cross-Validation in 'data_pipeline.py'** (`data_pipeline.py`)
  - *Problem:* Evaluating model metrics on a single random train/test split introduces sample-selection variance and can mask overfitting.
  - *Fix:* Validate model generalizability using `cross_val_score(model, X, y, cv=5)` or `StratifiedKFold`.
- **Missing 'stratify' in Classification train_test_split()** (`data_pipeline.py`)
  - *Problem:* Splitting classification data without `stratify=y` can skew class label distributions between train and test sets, especially with imbalanced classes.
  - *Fix:* Add `stratify=y` to `train_test_split(..., stratify=y)` to preserve identical class proportions in splits.
- **Sole Reliance on 'accuracy_score' in 'data_pipeline.py'** (`data_pipeline.py`)
  - *Problem:* Evaluating classification models using only raw accuracy can be deceptively optimistic on imbalanced datasets (e.g. trivial majority class predictions).
  - *Fix:* Include `classification_report`, `f1_score(average='weighted')`, or `roc_auc_score` for multi-metric evaluation.

## ⚙️ Sandbox Self-Verification Log
> **Verified by RepoDoctor Sandbox Engine:** Fixes are validated in an isolated environment before recommendation.

| Patch ID | Target File | Syntax Check | Pre-Tests | Post-Tests | Confidence | Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `QUAL-MUT-8557` | `model.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEP-UNPIN-numpy` | `requirements.txt` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEP-UNPIN-pandas` | `requirements.txt` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEP-DEPR-sklearn` | `requirements.txt` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEP-UNPIN-pytest` | `requirements.txt` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `SEC-EXEC-6719` | `model.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DOC-NOLICENSE` | `LICENSE` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `CICD-NOWORKFLOWS` | `.github/workflows/ci.yml` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEPLOY-NODOCKER` | `Dockerfile` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `DEPLOY-NOGITIGNORE` | `.gitignore` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `ML-LEAK-PREFIT-4727` | `data_pipeline.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `ML-LEAK-PREFIT-4727` | `data_pipeline.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `ML-VAL-NOSEED-1343` | `data_pipeline.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `ML-VAL-NOSEED-6295` | `data_pipeline.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |
| `ML-MET-NOSTRAT-7537` | `data_pipeline.py` | ✓ | 3P / 0F | 3P / 0F | 98% | **✅ PASSED** |

---
*Generated autonomously by [RepoDoctor AI](https://github.com/)* 🩺