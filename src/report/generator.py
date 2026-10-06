"""
RepoDoctor AI - Recruiter-Ready Engineering Report Generator
Generates Markdown and HTML executive diagnosis and verification reports.
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.core.models import RepositoryDiagnosis, Severity, ValidationStatus


class ReportGenerator:
    """Generates professional engineering reports ready for recruiters, tech leads, and CI summaries."""

    def __init__(self, diagnosis: RepositoryDiagnosis):
        self.diagnosis = diagnosis

    def generate_markdown(self) -> str:
        """Generate full GitHub Flavored Markdown report."""
        d = self.diagnosis
        sc = d.scorecard

        md = []
        md.append(f"# 🩺 RepoDoctor AI - Engineering Health Report")
        md.append(f"**Repository:** `{d.repo_name}` | **Date:** {d.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md.append(f"**Overall Health Score:** `{sc.overall_score} / 10.0` (Grade: **{sc.grade}**)")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 📊 Executive Summary")
        md.append(d.executive_summary)
        md.append("")

        # Score Breakdown Table
        md.append("## 🏆 Repository Scorecard")
        md.append("| Category | Score / 10 | Issues Found | Critical | Status |")
        md.append("| :--- | :---: | :---: | :---: | :--- |")
        for cat in sc.breakdown:
            status_emoji = "🟢" if cat.score >= 8.5 else "🟡" if cat.score >= 6.5 else "🔴"
            md.append(f"| **{cat.category.value}** | **{cat.score}** | {cat.issue_count} | {cat.critical_count} | {status_emoji} {cat.summary} |")

        md.append(f"| **OVERALL** | **`{sc.overall_score}`** | **{sc.total_issues}** | **{sc.critical_issues}** | **Grade: {sc.grade}** |")
        md.append("")

        # Critical & High Findings
        crit_high = [i for i in d.issues if i.severity in {Severity.CRITICAL, Severity.HIGH}]
        if crit_high:
            md.append("## 🚨 Critical & High Priority Findings")
            for i, issue in enumerate(crit_high, 1):
                sev_emoji = "🔥" if issue.severity == Severity.CRITICAL else "⚠️"
                md.append(f"### {i}. {sev_emoji} [{issue.severity.value}] {issue.title}")
                md.append(f"- **Location:** `{issue.file_path}` (Line: {issue.line_number or 'N/A'})")
                md.append(f"- **Confidence:** `{int(issue.confidence * 100)}%` | **Category:** `{issue.category.value}`")
                md.append(f"- **Risk Analysis:** {issue.risk_explanation}")
                if issue.code_snippet:
                    md.append("```python")
                    md.append(issue.code_snippet)
                    md.append("```")
                md.append(f"- **Recommended Fix:** {issue.recommendation}")
                md.append("")

        # ML Doctor Section
        ml_issues = [i for i in d.issues if i.category.value == "ML Engineering" or i.id.startswith("ML-")]
        if ml_issues:
            md.append("## 🧪 ML Doctor™ Diagnostics")
            md.append("Specialized machine learning integrity analysis:")
            for issue in ml_issues:
                md.append(f"- **{issue.title}** (`{issue.file_path}`)")
                md.append(f"  - *Problem:* {issue.risk_explanation}")
                md.append(f"  - *Fix:* {issue.recommendation}")
            md.append("")

        # Self-Verifying Sandbox Validation
        if d.validation_results:
            md.append("## ⚙️ Sandbox Self-Verification Log")
            md.append("> **Verified by RepoDoctor Sandbox Engine:** Fixes are validated in an isolated environment before recommendation.")
            md.append("")
            md.append("| Patch ID | Target File | Syntax Check | Pre-Tests | Post-Tests | Confidence | Result |")
            md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
            for vr in d.validation_results:
                v_emoji = "✅ PASSED" if vr.overall_status == ValidationStatus.PASSED else "❌ FAILED"
                md.append(f"| `{vr.patch_id}` | `{vr.file_path}` | {'✓' if vr.syntax_check else '✗'} | {vr.tests_passed_before}P / {vr.tests_failed_before}F | {vr.tests_passed_after}P / {vr.tests_failed_after}F | {int(vr.confidence * 100)}% | **{v_emoji}** |")
            md.append("")

        # Health Timeline
        if d.health_timeline:
            md.append("## 📈 Repository Health Timeline")
            md.append("| Version | Date | Overall Score | Issues | Fixes Applied | Description |")
            md.append("| :---: | :--- | :---: | :---: | :---: | :--- |")
            for entry in d.health_timeline:
                md.append(f"| **{entry.version}** | {entry.timestamp.strftime('%Y-%m-%d %H:%M')} | **{entry.overall_score} / 10** | {entry.total_issues} | {entry.fixes_applied} | {entry.description} |")
            md.append("")

        md.append("---")
        md.append("*Generated autonomously by [RepoDoctor AI](https://github.com/)* 🩺")
        return "\n".join(md)

    def generate_html(self) -> str:
        """Generate standalone styled HTML report."""
        d = self.diagnosis
        sc = d.scorecard
        md_content = self.generate_markdown()

        # Build clean modern HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoDoctor AI Report - {d.repo_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #0d1117;
            --surface: #161b22;
            --border: #30363d;
            --accent: #58a6ff;
            --text: #c9d1d9;
            --text-heading: #f0f6fc;
            --success: #3fb950;
            --warning: #d29922;
            --danger: #f85149;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        h1, h2, h3 {{ color: var(--text-heading); font-weight: 700; }}
        h1 {{ display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }}
        .badge-grade {{
            display: inline-block;
            background: linear-gradient(135deg, #1f6feb, #238636);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 800;
            font-size: 1.2rem;
        }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}
        .score-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .score-num {{ font-size: 2rem; font-weight: 800; color: var(--accent); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px 16px;
            border: 1px solid var(--border);
            text-align: left;
        }}
        th {{ background: rgba(255,255,255,0.05); color: var(--text-heading); }}
        code, pre {{
            font-family: 'JetBrains Mono', monospace;
            background: #090d13;
            border-radius: 6px;
        }}
        code {{ padding: 2px 6px; color: #79c0ff; }}
        pre {{ padding: 16px; overflow-x: auto; border: 1px solid var(--border); }}
        .callout {{
            border-left: 4px solid var(--accent);
            background: rgba(88, 166, 255, 0.1);
            padding: 16px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🩺 RepoDoctor AI Report: {d.repo_name}</h1>
        <p><strong>Generated:</strong> {d.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')} | <strong>Grade:</strong> <span class="badge-grade">{sc.grade} ({sc.overall_score}/10)</span></p>
        
        <div class="callout">
            <strong>Executive Summary:</strong> {d.executive_summary}
        </div>

        <h2>🏆 Scorecard Breakdown</h2>
        <div class="score-grid">
            <div class="score-card"><div class="score-num">{sc.overall_score}</div><div>Overall Health</div></div>
            <div class="score-card"><div class="score-num">{sc.total_issues}</div><div>Total Issues</div></div>
            <div class="score-card"><div class="score-num" style="color: var(--danger);">{sc.critical_issues}</div><div>Critical Findings</div></div>
            <div class="score-card"><div class="score-num" style="color: var(--success);">{len(d.validation_results)}</div><div>Verified Patches</div></div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Score / 10</th>
                    <th>Issues</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr><td><strong>{c.category.value}</strong></td><td><strong>{c.score}</strong></td><td>{c.issue_count}</td><td>{c.summary}</td></tr>" for c in sc.breakdown)}
            </tbody>
        </table>

        <h2>🚨 Findings & Diagnostics</h2>
        {''.join(f"<div style='margin-bottom: 20px; padding: 16px; border: 1px solid var(--border); border-radius: 8px;'><h3>[{i.severity.value}] {i.title}</h3><p><strong>File:</strong> <code>{i.file_path}:{i.line_number or 1}</code></p><p><strong>Risk:</strong> {i.risk_explanation}</p><p><strong>Recommendation:</strong> {i.recommendation}</p></div>" for i in d.issues[:8])}
    </div>
</body>
</html>"""
        return html
