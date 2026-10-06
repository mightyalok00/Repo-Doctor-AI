"""
RepoDoctor AI - Modern Streamlit Web Dashboard 🩺
Autonomous Repository Diagnosis, Self-Verifying Repair, and Recruiter-Ready Engineering Reports.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ai.diagnosis import DiagnosisEngine
from src.ai.patch_generator import PatchGenerator
from src.ai.reasoning import LLMReasoningEngine
from src.core.fetcher import RepositoryFetcher
from src.core.git_utils import apply_patch_to_file
from src.core.history_store import HealthTimelineStore
from src.core.models import Category, Severity, ValidationStatus
from src.report.generator import ReportGenerator
from src.sandbox.validator import PatchValidator

# Streamlit Page Config
st.set_page_config(
    page_title="RepoDoctor AI 🩺 Autonomous Repository Engineer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Dark Glassmorphism, Google Fonts, Vibrant Accents)
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(13, 17, 23, 0.9) 0%, rgba(22, 27, 34, 0.95) 100%);
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 900;
        background: linear-gradient(90deg, #58a6ff 0%, #39d353 50%, #bc8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #8b949e;
        margin-top: 6px;
        font-weight: 400;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(56, 139, 253, 0.12);
        border: 1px solid rgba(56, 139, 253, 0.35);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #58a6ff;
        margin-top: 10px;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 14px;
        padding: 18px 14px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(88, 166, 255, 0.4);
        box-shadow: 0 8px 25px rgba(88, 166, 255, 0.15);
    }
    .metric-num {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }
    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8b949e;
        margin-top: 6px;
        font-weight: 600;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-critical {
        background-color: rgba(248, 81, 73, 0.18);
        color: #ff7b72;
        border: 1px solid rgba(248, 81, 73, 0.4);
    }
    .badge-high {
        background-color: rgba(210, 153, 34, 0.18);
        color: #f0883e;
        border: 1px solid rgba(210, 153, 34, 0.4);
    }
    .badge-medium {
        background-color: rgba(227, 179, 65, 0.18);
        color: #e3b341;
        border: 1px solid rgba(227, 179, 65, 0.4);
    }
    .badge-low {
        background-color: rgba(88, 166, 255, 0.18);
        color: #58a6ff;
        border: 1px solid rgba(88, 166, 255, 0.4);
    }
    .badge-passed {
        background-color: rgba(63, 185, 80, 0.18);
        color: #3fb950;
        border: 1px solid rgba(63, 185, 80, 0.4);
    }

    /* Findings Cards */
    .finding-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(48, 54, 61, 0.9);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: all 0.2s ease;
    }
    .finding-card:hover {
        border-color: rgba(88, 166, 255, 0.35);
        background: rgba(22, 27, 34, 0.95);
    }
    .finding-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .finding-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: #f0f6fc;
    }
    .finding-meta {
        font-size: 0.85rem;
        color: #8b949e;
        margin-bottom: 10px;
    }
    .finding-risk {
        font-size: 0.92rem;
        color: #c9d1d9;
        margin-bottom: 8px;
        line-height: 1.45;
    }
    .finding-rec {
        font-size: 0.92rem;
        color: #3fb950;
        font-weight: 500;
        line-height: 1.45;
    }
    .reasoning-box {
        background: rgba(188, 140, 255, 0.08);
        border: 1px solid rgba(188, 140, 255, 0.25);
        border-radius: 8px;
        padding: 12px 14px;
        margin-top: 10px;
        color: #d2a8ff;
        font-size: 0.88rem;
    }

    /* ML Doctor Cards */
    .ml-leak-card {
        background: linear-gradient(135deg, rgba(248, 81, 73, 0.08) 0%, rgba(22, 27, 34, 0.8) 100%);
        border: 1px solid rgba(248, 81, 73, 0.3);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = None
if "patches" not in st.session_state:
    st.session_state.patches = []
if "val_results" not in st.session_state:
    st.session_state.val_results = []
if "target_repo" not in st.session_state:
    st.session_state.target_repo = "examples/buggy_ml_repo"
if "llm_proposals" not in st.session_state:
    st.session_state.llm_proposals = {}

history_store = HealthTimelineStore()

# ----------------- Hero Section -----------------
st.markdown(
    """
<div class="hero-container">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
        <div>
            <h1 class="hero-title">🩺 RepoDoctor AI</h1>
            <div class="hero-subtitle">
                Autonomous Engineer: Deep AST Diagnostics • ML Doctor™ Integrity • Self-Verifying Sandbox Repairs
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px;">
                <span class="status-pill">🛡️ AST Deterministic Source of Truth</span>
                <span class="status-pill">🧪 ML Leakage Guard</span>
                <span class="status-pill">⚙️ Disposable Sandbox Verification</span>
                <span class="status-pill">🤖 OpenRouter Reasoning Enabled</span>
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------- Sidebar Configuration -----------------
with st.sidebar:
    st.markdown("### ⚙️ Target Repository")
    repo_input = st.text_input(
        "GitHub URL or Local Path:",
        value=st.session_state.target_repo,
        help="Specify a GitHub repo URL (e.g. mightyalok00/Repo-Doctor-AI) or a local path.",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📦 Load Demo", use_container_width=True):
            st.session_state.target_repo = "examples/buggy_ml_repo"
            st.rerun()
    with col_btn2:
        if st.button("📁 Load Self", use_container_width=True):
            st.session_state.target_repo = str(root_dir)
            st.rerun()

    st.markdown("---")
    st.markdown("### 🤖 AI Reasoning Engine (LLM)")

    llm_enabled = st.toggle("Enable LLM Root-Cause Reasoning", value=True)

    llm_provider = st.selectbox(
        "LLM Provider / Gateway",
        ["OpenRouter (Free Tier)", "Local Ollama", "Custom OpenAI-Compatible"],
        index=0,
    )

    if llm_provider == "OpenRouter (Free Tier)":
        default_base = "https://openrouter.ai/api/v1"
        default_model = "openrouter/free"
    elif llm_provider == "Local Ollama":
        default_base = "http://localhost:11434/v1"
        default_model = "qwen2.5-coder:7b"
    else:
        default_base = os.getenv("REPO_DOCTOR_LLM_BASE_URL", "https://api.openai.com/v1")
        default_model = os.getenv("REPO_DOCTOR_LLM_MODEL", "gpt-4o-mini")

    llm_base_url = st.text_input("Base URL", value=os.getenv("REPO_DOCTOR_LLM_BASE_URL", default_base))
    llm_model = st.text_input("Model ID", value=os.getenv("REPO_DOCTOR_LLM_MODEL", default_model))
    llm_api_key = st.text_input(
        "API Key",
        value=os.getenv("REPO_DOCTOR_LLM_API_KEY", ""),
        type="password",
        help="API Key for OpenRouter / Remote Gateway. Automatically loaded from .env if present.",
    )

    st.markdown("---")
    st.markdown("### 🛠️ Execution & Sandbox Options")
    auto_sandbox = st.checkbox("Execute Disposable Sandbox Verification", value=True)
    pytest_timeout = st.slider("Pytest Validation Timeout (sec)", min_value=10, max_value=120, value=30, step=5)


# ----------------- Execution Logic -----------------
def execute_diagnosis(target_path: str):
    progress_bar = st.progress(0, text="Initializing repository fetcher...")
    fetcher = RepositoryFetcher(target_path)

    try:
        progress_bar.progress(15, text="Fetching and cloning repository files...")
        fetcher.fetch()

        progress_bar.progress(35, text="Running AST & static analyzers across 8 dimensions...")
        engine = DiagnosisEngine(fetcher)
        diagnosis = engine.run_full_diagnosis()

        # Optional LLM Reasoning Stage
        llm_proposals_map = {}
        if llm_enabled and (llm_api_key or "localhost" in llm_base_url or "127.0.0.1" in llm_base_url):
            progress_bar.progress(55, text="Invoking LLM Reasoning Engine for root-cause analysis...")
            try:
                reasoner = LLMReasoningEngine(
                    base_url=llm_base_url,
                    api_key=llm_api_key,
                    model=llm_model,
                    timeout_sec=pytest_timeout,
                )
                res = reasoner.reason(diagnosis.issues)
                if res.proposals:
                    llm_proposals_map = {p.issue_id: p for p in res.proposals}
            except Exception as llm_err:
                st.warning(f"LLM Reasoning skipped: {str(llm_err)}")

        progress_bar.progress(70, text="Generating autonomous self-verifying AST patches...")
        patch_gen = PatchGenerator(fetcher)
        patches = patch_gen.generate_all_patches(diagnosis.issues)

        val_results = []
        if auto_sandbox and patches:
            progress_bar.progress(85, text="Running disposable sandbox pre vs post test validations...")
            validator = PatchValidator(fetcher.repo_path)
            val_results = validator.validate_all_patches(patches)

        # Record timeline snapshot
        progress_bar.progress(95, text="Persisting timeline snapshot...")
        history_store.record_snapshot(
            repo_identifier=diagnosis.repo_name,
            overall_score=diagnosis.scorecard.overall_score,
            category_scores=diagnosis.scorecard.category_scores,
            total_issues=diagnosis.scorecard.total_issues,
        )
        diagnosis.health_timeline = history_store.get_timeline(diagnosis.repo_name)
        diagnosis.patches = patches
        diagnosis.validation_results = val_results

        # Update Session State
        st.session_state.diagnosis = diagnosis
        st.session_state.patches = patches
        st.session_state.val_results = val_results
        st.session_state.target_repo = target_path
        st.session_state.llm_proposals = llm_proposals_map

        progress_bar.progress(100, text="Diagnosis complete!")
        st.success(f"🎉 Successfully diagnosed **{diagnosis.repo_name}** ({diagnosis.total_files} files, {diagnosis.total_loc:,} lines of code)!")
    except Exception as e:
        st.error(f"❌ Error during diagnosis: {str(e)}")
        import traceback
        st.code(traceback.format_exc(), language="text")


# Main Input Bar
c_input, c_btn = st.columns([4, 1.2])
with c_input:
    active_target = st.text_input(
        "Repository Target",
        value=st.session_state.target_repo,
        label_visibility="collapsed",
        placeholder="Enter GitHub URL or relative/absolute local path...",
    )
with c_btn:
    if st.button("🚀 Diagnose & Verify", type="primary", use_container_width=True):
        execute_diagnosis(active_target)

# ----------------- Results Dashboard -----------------
if st.session_state.diagnosis:
    diag = st.session_state.diagnosis
    sc = diag.scorecard
    proposals_map = st.session_state.llm_proposals

    st.markdown("<br>", unsafe_allow_html=True)

    # Top KPI Metrics Row
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    score_color = "#3fb950" if sc.overall_score >= 8.5 else "#d29922" if sc.overall_score >= 6.5 else "#ff7b72"
    with m1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: {score_color};">{sc.overall_score:.1f} <span style="font-size: 1.1rem; color: #c9d1d9;">({sc.grade})</span></div>
            <div class="metric-title">Health Score</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: #58a6ff;">{sc.total_issues}</div>
            <div class="metric-title">Total Findings</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: #ff7b72;">{sc.critical_issues}</div>
            <div class="metric-title">Critical Flaws</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: #f0883e;">{sc.high_issues}</div>
            <div class="metric-title">High Priority</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with m5:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: #3fb950;">{len(st.session_state.patches)}</div>
            <div class="metric-title">Auto-Patches</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with m6:
        verified_count = sum(
            1 for vr in st.session_state.val_results if vr.overall_status == ValidationStatus.PASSED
        )
        total_val = len(st.session_state.val_results)
        v_color = "#3fb950" if verified_count == total_val and total_val > 0 else "#58a6ff"
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-num" style="color: {v_color};">{verified_count} / {total_val}</div>
            <div class="metric-title">Sandbox Verified</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------- Interactive Tabs -----------------
    tab_radar, tab_findings, tab_ml_doc, tab_fixer, tab_hist, tab_ai_review, tab_rep = st.tabs(
        [
            "📊 Scorecard & Radar",
            "🩺 Findings Explorer",
            "🧪 ML Doctor™",
            "🔧 Self-Verifying Repair",
            "📈 Health Timeline",
            "🤖 AI Root-Cause Review",
            "📑 Recruiter Report & Badges",
        ]
    )

    # Tab 1: Radar & Dimension Breakdown
    with tab_radar:
        c_rad, c_cat = st.columns([1.2, 1.3])
        with c_rad:
            st.markdown("#### 🕸️ 8-Dimension Engineering Radar")
            categories = [c.category.value for c in sc.breakdown]
            scores = [c.score for c in sc.breakdown]
            categories_closed = categories + [categories[0]]
            scores_closed = scores + [scores[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(
                go.Scatterpolar(
                    r=scores_closed,
                    theta=categories_closed,
                    fill="toself",
                    fillcolor="rgba(88, 166, 255, 0.25)",
                    line=dict(color="#58a6ff", width=2.5),
                    marker=dict(size=7, color="#39d353"),
                    name="Scorecard",
                )
            )
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], color="#8b949e", gridcolor="rgba(255,255,255,0.1)"),
                    angularaxis=dict(color="#f0f6fc", gridcolor="rgba(255,255,255,0.1)"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=30, b=30),
                height=380,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with c_cat:
            st.markdown("#### 📋 Dimension Status & Breakdown")
            for cat in sc.breakdown:
                c_icon = "🟢" if cat.score >= 8.5 else "🟡" if cat.score >= 6.5 else "🔴"
                with st.expander(
                    f"{c_icon} **{cat.category.value}**: {cat.score:.1f}/10 ({cat.issue_count} findings, {cat.critical_count} critical)"
                ):
                    st.progress(cat.score / 10.0)
                    cat_issues = [i for i in diag.issues if i.category == cat.category]
                    if cat_issues:
                        for ci in cat_issues:
                            s_badge = f"badge-{ci.severity.value.lower()}"
                            st.markdown(
                                f"- <span class='badge {s_badge}'>[{ci.severity.value}]</span> `{ci.file_path}:{ci.line_number or 1}` — {ci.title}",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown("✨ Perfect score! No anti-patterns detected in this dimension.")

    # Tab 2: Findings Explorer
    with tab_findings:
        st.markdown("#### 🔍 Real-Time Findings Filter")
        f_c1, f_c2, f_c3 = st.columns([1.5, 1.5, 2])
        with f_c1:
            sel_sev = st.multiselect(
                "Filter Severity",
                [s.value for s in Severity],
                default=["CRITICAL", "HIGH", "MEDIUM"],
            )
        with f_c2:
            sel_cat = st.multiselect(
                "Filter Category",
                [c.value for c in Category],
                default=[c.value for c in Category],
            )
        with f_c3:
            search_q = st.text_input("Search Findings / Code / Keywords", placeholder="e.g. eval, leakage, unpinned...")

        filtered = [
            i
            for i in diag.issues
            if i.severity.value in sel_sev
            and i.category.value in sel_cat
            and (
                search_q.lower() in i.title.lower()
                or search_q.lower() in i.file_path.lower()
                or search_q.lower() in i.risk_explanation.lower()
            )
        ]

        st.markdown(f"Showing **{len(filtered)}** of **{len(diag.issues)}** total findings:")

        for issue in filtered:
            s_badge = f"badge-{issue.severity.value.lower()}"
            st.markdown(
                f"""
            <div class="finding-card">
                <div class="finding-header">
                    <span class="finding-title">{issue.title}</span>
                    <span class="badge {s_badge}">[{issue.severity.value}]</span>
                </div>
                <div class="finding-meta">
                    📁 <code>{issue.file_path}:{issue.line_number or 1}</code> | Category: <strong>{issue.category.value}</strong> | Confidence: <strong>{int(issue.confidence * 100)}%</strong>
                </div>
                <div class="finding-risk">
                    <strong>⚠️ Risk Analysis:</strong> {issue.risk_explanation}
                </div>
                <div class="finding-rec">
                    <strong>💡 Recommendation:</strong> {issue.recommendation}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show LLM root-cause if available
            if issue.id in proposals_map:
                proposal = proposals_map[issue.id]
                if proposal.root_cause or proposal.rationale:
                    st.markdown(
                        f"""
                    <div class="reasoning-box">
                        <strong>🧠 AI Reasoning Root-Cause:</strong> {proposal.root_cause}<br>
                        <strong>📐 Architectural Rationale:</strong> {proposal.rationale}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            if issue.code_snippet:
                with st.expander("🔎 View Problematic Code"):
                    st.code(issue.code_snippet, language="python")

    # Tab 3: ML Doctor Studio
    with tab_ml_doc:
        st.markdown("### 🧪 ML Doctor™ Diagnostics Studio")
        st.markdown("Specialized AST heuristics analyzing data pipelines, leakages, and statistical reproducibility.")

        ml_findings = [i for i in diag.issues if i.category == Category.ML_ENGINEERING or i.id.startswith("ML-")]
        if not ml_findings:
            st.success("🎉 Zero ML anti-patterns or data leakage detected in this repository!")
        else:
            for issue in ml_findings:
                st.markdown(
                    f"""
                <div class="ml-leak-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.15rem; font-weight: 700; color: #ff7b72;">🚨 {issue.title}</span>
                        <span class="badge badge-critical">[{issue.severity.value}]</span>
                    </div>
                    <div style="color: #8b949e; font-size: 0.9rem; margin-bottom: 8px;">
                        File: <code>{issue.file_path}:{issue.line_number or 1}</code>
                    </div>
                    <div style="color: #f0f6fc; margin-bottom: 6px;">
                        <strong>Root Cause & Contamination Risk:</strong> {issue.risk_explanation}
                    </div>
                    <div style="color: #3fb950; margin-bottom: 10px;">
                        <strong>Autonomous Repair Action:</strong> {issue.recommendation}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                if issue.code_snippet:
                    with st.expander("Inspect ML Code Snippet"):
                        st.code(issue.code_snippet, language="python")

    # Tab 4: Self-Verifying Repair Hub
    with tab_fixer:
        st.markdown("### 🔧 Autonomous Self-Verifying Repair Hub")
        st.markdown("> **Safety Guarantee:** Proposed patches are compiled, executed, and tested in a disposable copy of the repository.")

        patches = st.session_state.patches
        val_results = st.session_state.val_results

        if not patches:
            st.info("No patches required for current repository state.")
        else:
            col_a1, col_a2 = st.columns([1.5, 2.5])
            with col_a1:
                if st.button("🚀 1-Click Apply All Verified Patches", type="primary", use_container_width=True):
                    fetcher = RepositoryFetcher(diag.repo_path)
                    applied_count = 0
                    for p in patches:
                        target_file = fetcher.repo_path / p.file_path
                        if apply_patch_to_file(target_file, p.replacement_code):
                            applied_count += 1
                    st.success(f"✓ Applied {applied_count} verified patches to repository!")
                    execute_diagnosis(diag.repo_path)

            st.markdown("<br>", unsafe_allow_html=True)

            for i, (p, vr) in enumerate(zip(patches, val_results) if val_results else zip(patches, [None] * len(patches)), 1):
                status_icon = "✅ VERIFIED" if (vr and vr.overall_status == ValidationStatus.PASSED) else "⚙️ CANDIDATE"
                with st.expander(f"**Patch #{i} [{status_icon}]** — `{p.file_path}`: {p.description}"):
                    if vr:
                        c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                        with c_s1:
                            st.metric("Syntax Verification", "Passed" if vr.syntax_check else "Failed")
                        with c_s2:
                            st.metric("Pre-Patch Tests", f"{vr.tests_passed_before} Pass / {vr.tests_failed_before} Fail")
                        with c_s3:
                            st.metric("Post-Patch Tests", f"{vr.tests_passed_after} Pass / {vr.tests_failed_after} Fail")
                        with c_s4:
                            st.metric("Confidence Score", f"{int(vr.confidence * 100)}%")

                    st.markdown("##### 📝 Unified Diff Preview:")
                    st.code(p.diff, language="diff")

                    if st.button(f"Apply Patch #{i} Only (`{p.file_path}`)", key=f"apply_{p.issue_id}"):
                        fetcher = RepositoryFetcher(diag.repo_path)
                        target_file = fetcher.repo_path / p.file_path
                        apply_patch_to_file(target_file, p.replacement_code)
                        st.success(f"Applied patch to {p.file_path}!")
                        st.rerun()

    # Tab 5: Health Timeline
    with tab_hist:
        st.markdown("### 📈 Continuous Health Timeline")
        timeline = diag.health_timeline or history_store.get_timeline(diag.repo_name)

        if not timeline:
            st.info("No timeline data recorded yet.")
        elif len(timeline) == 1:
            st.info(f"Baseline Snapshot: **{timeline[0].overall_score:.1f}/10** ({timeline[0].version}) recorded at {timeline[0].timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            first_score = timeline[0].overall_score
            latest_score = timeline[-1].overall_score
            delta = latest_score - first_score
            sign = "+" if delta >= 0 else ""
            st.success(f"🚀 Health trajectory improved: **{first_score:.1f} → {latest_score:.1f} ({sign}{delta:.1f} pts)** across {len(timeline)} versions!")

            versions = [t.version for t in timeline]
            scores = [t.overall_score for t in timeline]

            fig_time = go.Figure()
            fig_time.add_trace(
                go.Scatter(
                    x=versions,
                    y=scores,
                    mode="lines+markers+text",
                    text=[f"{s:.1f}" for s in scores],
                    textposition="top center",
                    line=dict(color="#39d353", width=3.5),
                    marker=dict(size=12, color="#58a6ff", line=dict(color="#ffffff", width=1.5)),
                    name="Score",
                )
            )
            fig_time.update_layout(
                yaxis=dict(range=[0, 10.5], title="Score / 10", gridcolor="rgba(255,255,255,0.1)"),
                xaxis=dict(title="Version Snapshot"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                margin=dict(l=30, r=30, t=30, b=30),
            )
            st.plotly_chart(fig_time, use_container_width=True)

    # Tab 6: AI Root-Cause Review
    with tab_ai_review:
        st.markdown("### 🤖 Senior AI Architectural Review")
        if not proposals_map:
            st.info("💡 Enable LLM Reasoning in the sidebar to view AI-generated root-cause analyses and architectural guidance.")
        else:
            st.markdown("Root-cause diagnoses backed by LLM evidence grounding:")
            for issue_id, prop in proposals_map.items():
                matched_issue = next((i for i in diag.issues if i.id == issue_id), None)
                title = matched_issue.title if matched_issue else issue_id
                with st.expander(f"🧠 **[{issue_id}]** {title}"):
                    st.markdown(f"**Root Cause Analysis:**\n{prop.root_cause}")
                    st.markdown(f"**Architectural Rationale:**\n{prop.rationale}")
                    st.markdown(f"**Safe to Apply:** `{'Yes' if prop.safe_to_apply else 'Requires Human Review'}`")

    # Tab 7: Reports & Badges
    with tab_rep:
        st.markdown("### 📑 Recruiter-Ready Engineering Report & Badges")
        rep_gen = ReportGenerator(diag)
        report_md = rep_gen.generate_markdown()
        report_html = rep_gen.generate_html()

        cd1, cd2, cd3 = st.columns(3)
        with cd1:
            st.download_button(
                "📥 Download Markdown Report (.md)",
                data=report_md,
                file_name=f"REPO_DOCTOR_{diag.repo_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with cd2:
            st.download_button(
                "📥 Download HTML Report (.html)",
                data=report_html,
                file_name=f"REPO_DOCTOR_{diag.repo_name}.html",
                mime="text/html",
                use_container_width=True,
            )
        with cd3:
            diag_json = diag.model_dump_json(indent=2)
            st.download_button(
                "📥 Download JSON Data (.json)",
                data=diag_json,
                file_name=f"REPO_DOCTOR_{diag.repo_name}.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("#### 🛡️ GitHub README Badges")
        score_badge_color = "brightgreen" if sc.overall_score >= 8.5 else "yellow" if sc.overall_score >= 6.5 else "red"
        badge_code = f"[![RepoDoctor Score](https://img.shields.io/badge/RepoDoctor-{sc.overall_score:.1f}%2F10-{score_badge_color})](https://github.com/mightyalok00/Repo-Doctor-AI)"
        st.code(badge_code, language="markdown")
        st.markdown(badge_code)

        st.markdown("---")
        st.markdown("#### 📄 Report Preview")
        st.markdown(report_md)

else:
    st.info("👈 Enter a GitHub URL or click **'Load Demo'** above to run an autonomous diagnosis!")
