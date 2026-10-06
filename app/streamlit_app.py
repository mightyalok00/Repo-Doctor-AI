"""
RepoDoctor AI - Streamlit Web Dashboard 🩺
Autonomous Repository Diagnosis, Self-Verifying Repair, and Recruiter-Ready Engineering Reports.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from src.core.fetcher import RepositoryFetcher
from src.ai.diagnosis import DiagnosisEngine
from src.ai.patch_generator import PatchGenerator
from src.sandbox.validator import PatchValidator
from src.core.history_store import HealthTimelineStore
from src.report.generator import ReportGenerator
from src.core.models import Severity, Category, ValidationStatus
from src.core.git_utils import apply_patch_to_file

# Streamlit Page Config
st.set_page_config(
    page_title="RepoDoctor AI 🩺 Autonomous Repository Engineer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark glassmorphism
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #3fb950, #d2a8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .tagline {
        font-size: 1.1rem;
        color: #8b949e;
        margin-bottom: 20px;
    }
    .metric-box {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-critical {
        background-color: #f8514933;
        color: #ff7b72;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #f8514966;
    }
    .badge-high {
        background-color: #d2992233;
        color: #e3b341;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #d2992266;
    }
    .badge-passed {
        background-color: #23863633;
        color: #3fb950;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid #23863666;
    }
    .card-finding {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = None
if "patches" not in st.session_state:
    st.session_state.patches = []
if "val_results" not in st.session_state:
    st.session_state.val_results = []
if "target_repo" not in st.session_state:
    st.session_state.target_repo = "examples/buggy_ml_repo"

history_store = HealthTimelineStore()

# Header
st.markdown('<div class="main-header">RepoDoctor AI 🩺</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">An AI-powered autonomous engineer that diagnoses, scores, and repairs GitHub repositories.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Target Repository")
    repo_input = st.text_input(
        "Enter GitHub URL or Local Path:",
        value=st.session_state.target_repo,
        help="Provide a GitHub repository URL or a relative/absolute local directory path."
    )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        use_demo = st.button("📦 Load Demo Repo", use_container_width=True)
    with col_b2:
        use_self = st.button("📁 Load Current Repo", use_container_width=True)

    if use_demo:
        repo_input = "examples/buggy_ml_repo"
        st.session_state.target_repo = repo_input
    if use_self:
        repo_input = str(root_dir)
        st.session_state.target_repo = repo_input

    st.markdown("---")
    st.subheader("💡 Analysis Settings")
    auto_sandbox = st.checkbox("Execute Sandbox Verification", value=True, help="Automatically run tests before and after applying patches.")
    st.info("⚡ ML Doctor analyzes AST pipelines for data leakage, unstratified splits, and missing seeds.")


def run_scan(target_path: str):
    with st.spinner(f"🩺 RepoDoctor inspecting '{target_path}'..."):
        fetcher = RepositoryFetcher(target_path)
        try:
            fetcher.fetch()
            engine = DiagnosisEngine(fetcher)
            diagnosis = engine.run_full_diagnosis()

            # Record timeline
            history_store.record_snapshot(
                repo_identifier=diagnosis.repo_name,
                overall_score=diagnosis.scorecard.overall_score,
                category_scores=diagnosis.scorecard.category_scores,
                total_issues=diagnosis.scorecard.total_issues
            )
            diagnosis.health_timeline = history_store.get_timeline(diagnosis.repo_name)

            # Generate patches
            patch_gen = PatchGenerator(fetcher)
            patches = patch_gen.generate_all_patches(diagnosis.issues)

            val_results = []
            if auto_sandbox and patches:
                validator = PatchValidator(fetcher.repo_path)
                val_results = validator.validate_all_patches(patches)

            diagnosis.patches = patches
            diagnosis.validation_results = val_results

            st.session_state.diagnosis = diagnosis
            st.session_state.patches = patches
            st.session_state.val_results = val_results
            st.session_state.target_repo = target_path
            st.success("✓ Repository diagnosis completed successfully!")
        except Exception as e:
            st.error(f"Error scanning repository: {str(e)}")


# Main Scan Action
c_inp, c_act = st.columns([4, 1])
with c_inp:
    active_target = st.text_input("Repository Target", value=repo_input, label_visibility="collapsed")
with c_act:
    if st.button("🔍 Diagnose Repository", type="primary", use_container_width=True):
        run_scan(active_target)

# Display Diagnosis if available
if st.session_state.diagnosis:
    diag = st.session_state.diagnosis
    sc = diag.scorecard

    st.markdown("---")

    # Metrics Summary Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        grade_color = "#3fb950" if sc.overall_score >= 8.5 else "#d29922" if sc.overall_score >= 6.5 else "#f85149"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color: {grade_color};">{sc.overall_score} <span style="font-size: 1.2rem;">({sc.grade})</span></div>
            <div class="metric-label">Overall Health</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value">{sc.total_issues}</div>
            <div class="metric-label">Total Findings</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color: #ff7b72;">{sc.critical_issues}</div>
            <div class="metric-label">Critical Issues</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color: #3fb950;">{len(st.session_state.patches)}</div>
            <div class="metric-label">Auto-Fixes Available</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        verified_count = sum(1 for vr in st.session_state.val_results if vr.overall_status == ValidationStatus.PASSED)
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value" style="color: #58a6ff;">{verified_count} / {len(st.session_state.val_results)}</div>
            <div class="metric-label">Sandbox Verified</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    tab_diag, tab_ml, tab_fix, tab_timeline, tab_report = st.tabs([
        "🩺 Findings & Scorecard",
        "🧪 ML Doctor™",
        "🔧 Fix My Repo (Self-Verifying)",
        "📈 Health Timeline",
        "📑 Recruiter Report"
    ])

    with tab_diag:
        col_radar, col_table = st.columns([1.1, 1.3])

        with col_radar:
            st.subheader("🕸️ Engineering Radar Scorecard")
            categories = [c.category.value for c in sc.breakdown]
            scores = [c.score for c in sc.breakdown]
            # Close the polygon
            categories_closed = categories + [categories[0]]
            scores_closed = scores + [scores[0]]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=scores_closed,
                theta=categories_closed,
                fill='toself',
                fillcolor='rgba(88, 166, 255, 0.2)',
                line=dict(color='#58a6ff', width=2),
                name='Repository Health'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], color="#8b949e"),
                    angularaxis=dict(color="#c9d1d9")
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=30, r=30, t=20, b=20),
                height=340
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.subheader("📋 Dimension Breakdown")
            for cat in sc.breakdown:
                c_icon = "🟢" if cat.score >= 8.5 else "🟡" if cat.score >= 6.5 else "🔴"
                with st.expander(f"{c_icon} **{cat.category.value}**: {cat.score}/10 — {cat.issue_count} findings ({cat.critical_count} critical)"):
                    cat_issues = [i for i in diag.issues if i.category == cat.category]
                    if cat_issues:
                        for ci in cat_issues:
                            st.markdown(f"- **[{ci.severity.value}]** `{ci.file_path}`: {ci.title}")
                    else:
                        st.markdown("✨ No anti-patterns found in this category.")

        st.markdown("---")
        st.subheader("🚨 Filtered Findings List")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            sev_filter = st.multiselect("Filter by Severity", [s.value for s in Severity], default=["CRITICAL", "HIGH", "MEDIUM"])
        with c_f2:
            cat_filter = st.multiselect("Filter by Category", [c.value for c in Category], default=[c.value for c in Category])

        filtered_issues = [i for i in diag.issues if i.severity.value in sev_filter and i.category.value in cat_filter]

        if not filtered_issues:
            st.info("No issues match the selected filters.")
        else:
            for issue in filtered_issues:
                sev_badge = "badge-critical" if issue.severity == Severity.CRITICAL else "badge-high"
                st.markdown(f"""
                <div class="card-finding">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: #f0f6fc;">{issue.title}</span>
                        <span class="{sev_badge}">[{issue.severity.value}]</span>
                    </div>
                    <div style="color: #8b949e; font-size: 0.9rem; margin-bottom: 8px;">
                        📁 <code>{issue.file_path}:{issue.line_number or 1}</code> | Category: <strong>{issue.category.value}</strong> | Confidence: <strong>{int(issue.confidence*100)}%</strong>
                    </div>
                    <div style="margin-bottom: 8px; color: #c9d1d9;">
                        <strong>Risk:</strong> {issue.risk_explanation}
                    </div>
                    <div style="color: #3fb950;">
                        <strong>Recommended Fix:</strong> {issue.recommendation}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if issue.code_snippet:
                    with st.expander("View Code Snippet"):
                        st.code(issue.code_snippet, language="python")

    with tab_ml:
        st.subheader("🧪 ML Project Doctor Diagnostics")
        st.markdown("Specialized AST analysis tailored for Data Science & ML engineering pipelines:")

        ml_issues = [i for i in diag.issues if i.category.value == "ML Engineering" or i.id.startswith("ML-")]
        if not ml_issues:
            st.success("✓ No ML anti-patterns or data leakage detected in this repository!")
        else:
            for issue in ml_issues:
                st.error(f"⚠️ **{issue.title}** (in `{issue.file_path}`)")
                st.markdown(f"**Root Cause & Risk:** {issue.risk_explanation}")
                if issue.code_snippet:
                    st.code(issue.code_snippet, language="python")
                st.markdown(f"**ML Best Practice Recommendation:** {issue.recommendation}")
                st.markdown("---")

    with tab_fix:
        st.subheader("🔧 Autonomous Repair & Sandbox Self-Verification")
        st.markdown("> **Self-Verifying Guarantee:** RepoDoctor tests candidate patches in a sandbox before confirming their validity.")

        patches = st.session_state.patches
        val_results = st.session_state.val_results

        if not patches:
            st.info("No automated patches needed for current repository state.")
        else:
            col_act1, col_act2 = st.columns([2, 3])
            with col_act1:
                if st.button("🚀 1-Click Apply All Verified Patches to Repository", type="primary", use_container_width=True):
                    fetcher = RepositoryFetcher(diag.repo_path)
                    for p in patches:
                        target_file = fetcher.repo_path / p.file_path
                        apply_patch_to_file(target_file, p.replacement_code)
                    st.success("✓ Successfully applied all verified patches!")
                    # Re-scan
                    run_scan(diag.repo_path)

            st.markdown("<br>", unsafe_allow_html=True)

            # Verification Results Table
            if val_results:
                st.subheader("⚙️ Sandbox Verification Checklist")
                for p, vr in zip(patches, val_results):
                    v_icon = "✅ VERIFIED" if vr.overall_status == ValidationStatus.PASSED else "❌ FAILED"
                    with st.expander(f"**{v_icon}** — `{p.file_path}`: {p.description}"):
                        c_v1, c_v2, c_v3 = st.columns(3)
                        with c_v1:
                            st.write(f"**Syntax Check:** {'✓ Passed' if vr.syntax_check else '✗ Failed'}")
                        with c_v2:
                            st.write(f"**Pre-Patch Tests:** {vr.tests_passed_before} Passed / {vr.tests_failed_before} Failed")
                        with c_v3:
                            st.write(f"**Post-Patch Tests:** {vr.tests_passed_after} Passed / {vr.tests_failed_after} Failed")

                        st.markdown("**Unified Diff:**")
                        st.code(p.diff, language="diff")

    with tab_timeline:
        st.subheader("📈 Repository Health Timeline")
        timeline = diag.health_timeline or history_store.get_timeline(diag.repo_name)

        if len(timeline) <= 1:
            st.info("Repository health timeline tracks improvements over successive scans and repair iterations.")
            if timeline:
                st.write(f"Initial baseline snapshot: **{timeline[0].overall_score}/10** ({timeline[0].version})")
        else:
            first_score = timeline[0].overall_score
            latest_score = timeline[-1].overall_score
            total_fixes = sum(t.fixes_applied for t in timeline)
            st.success(f"🚀 Your repository improved from **{first_score:.1f} → {latest_score:.1f}** after **{total_fixes} automated fixes**!")

            # Timeline chart
            versions = [t.version for t in timeline]
            scores = [t.overall_score for t in timeline]
            dates = [t.timestamp.strftime("%b %d, %H:%M") for t in timeline]

            fig_t = go.Figure()
            fig_t.add_trace(go.Scatter(
                x=versions,
                y=scores,
                mode='lines+markers+text',
                text=[f"{s:.1f}" for s in scores],
                textposition="top center",
                line=dict(color='#3fb950', width=3),
                marker=dict(size=12, color='#58a6ff')
            ))
            fig_t.update_layout(
                yaxis=dict(range=[0, 10.5], title="Score / 10", gridcolor='rgba(255,255,255,0.1)'),
                xaxis=dict(title="Version Snapshot"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_t, use_container_width=True)

    with tab_report:
        st.subheader("📑 Recruiter-Ready Engineering Report")
        rep_gen = ReportGenerator(diag)
        report_md = rep_gen.generate_markdown()

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.download_button(
                "📥 Download Markdown Report (.md)",
                data=report_md,
                file_name=f"REPO_DOCTOR_{diag.repo_name}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with c_d2:
            st.download_button(
                "📥 Download HTML Report (.html)",
                data=rep_gen.generate_html(),
                file_name=f"REPO_DOCTOR_{diag.repo_name}.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown(report_md)
else:
    st.info("👈 Enter a GitHub URL or click 'Load Demo Repo' above to diagnose and repair!")
