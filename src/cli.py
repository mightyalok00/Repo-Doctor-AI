"""
RepoDoctor AI - Command Line Interface (CLI)
Provides rich interactive terminal commands for scanning, diagnosing, and repairing repositories.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Force UTF-8 stdout encoding for Windows console compatibility
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console(force_terminal=True, legacy_windows=False)

from src.ai.diagnosis import DiagnosisEngine
from src.ai.patch_generator import PatchGenerator
from src.core.fetcher import RepositoryFetcher
from src.core.git_utils import apply_patch_to_file
from src.core.history_store import HealthTimelineStore
from src.core.models import Severity
from src.report.generator import ReportGenerator
from src.sandbox.validator import PatchValidator


def render_banner():
    banner_text = """[bold cyan]
  ____                     ____             _               _     ___ 
 |  _ \\ ___ _ __   ___    |  _ \\  ___   ___| |_ ___  _ __  / \\   |_ _|
 | |_) / _ \\ '_ \\ / _ \\   | | | |/ _ \\ / __| __/ _ \\| '__|/ _ \\   | | 
 |  _ <  __/ |_) | (_) |  | |_| | (_) | (__| || (_) | |  / ___ \\  | | 
 |_| \\_\\___| .__/ \\___/   |____/ \\___/ \\___|\\__\\___/|_| /_/   \\_\\|___|
           |_|                                                        
[/bold cyan][dim]Autonomous AI Engineer: Diagnose, Score, Repair & Validate Repositories[/dim]
"""
    console.print(banner_text)


def scan_command(target: str):
    render_banner()
    with console.status(f"[green]Scanning & diagnosing repository '{target}'...[/green]"):
        fetcher = RepositoryFetcher(target)
        fetcher.fetch()
        engine = DiagnosisEngine(fetcher)
        diagnosis = engine.run_full_diagnosis()

        # Record timeline
        store = HealthTimelineStore()
        store.record_snapshot(
            repo_identifier=diagnosis.repo_name,
            overall_score=diagnosis.scorecard.overall_score,
            category_scores=diagnosis.scorecard.category_scores,
            total_issues=diagnosis.scorecard.total_issues
        )
        diagnosis.health_timeline = store.get_timeline(diagnosis.repo_name)

    # Print Scorecard Table
    sc = diagnosis.scorecard
    table = Table(title=f"📊 Repo Scorecard: {diagnosis.repo_name} (Overall: {sc.overall_score}/10 | Grade: {sc.grade})", show_lines=True)
    table.add_column("Category", style="cyan bold")
    table.add_column("Score / 10", justify="center")
    table.add_column("Issues", justify="center")
    table.add_column("Critical", justify="center")
    table.add_column("Health Status")

    for cat in sc.breakdown:
        score_style = "green bold" if cat.score >= 8.5 else "yellow bold" if cat.score >= 6.5 else "red bold"
        status_icon = "🟢" if cat.score >= 8.5 else "🟡" if cat.score >= 6.5 else "🔴"
        table.add_row(
            cat.category.value,
            f"[{score_style}]{cat.score}[/{score_style}]",
            str(cat.issue_count),
            f"[red]{cat.critical_count}[/red]" if cat.critical_count > 0 else "0",
            f"{status_icon} {cat.summary}"
        )

    console.print(table)
    console.print()

    # Print Key Issues
    if diagnosis.issues:
        console.print(f"[bold yellow]Found {len(diagnosis.issues)} findings across code, security, and ML pipelines:[/bold yellow]")
        for idx, issue in enumerate(diagnosis.issues[:6], 1):
            sev_color = "red bold" if issue.severity == Severity.CRITICAL else "yellow bold" if issue.severity == Severity.HIGH else "cyan"
            p = Panel(
                f"[bold]{issue.risk_explanation}[/bold]\n\n"
                f"[dim]File:[/dim] {issue.file_path}:{issue.line_number or 1}\n"
                f"[dim]Recommendation:[/dim] [green]{issue.recommendation}[/green]\n"
                f"[dim]Confidence:[/dim] {int(issue.confidence * 100)}%",
                title=f"[{sev_color}][{issue.severity.value}] {issue.title}[/{sev_color}]",
                border_style="dim"
            )
            console.print(p)

    console.print(Panel(diagnosis.executive_summary, title="[bold green]Executive Diagnosis Summary[/bold green]"))


def fix_command(target: str, apply_fixes: bool = False):
    render_banner()
    console.print(f"[bold green]Initiating Autonomous Repair & Sandbox Validation for '{target}'...[/bold green]\n")

    fetcher = RepositoryFetcher(target)
    fetcher.fetch()

    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)

    if not patches:
        console.print("[green]✓ No auto-fixable issues detected or all checks passed.[/green]")
        return

    console.print(f"[cyan]Generated {len(patches)} candidate patches. Entering Sandbox Validator...[/cyan]\n")

    validator = PatchValidator(fetcher.repo_path)
    val_results = validator.validate_all_patches(patches)

    val_table = Table(title="⚙️ Sandbox Self-Verification Results", show_lines=True)
    val_table.add_column("Patch ID", style="cyan")
    val_table.add_column("Target File")
    val_table.add_column("Syntax Check", justify="center")
    val_table.add_column("Tests (Before -> After)", justify="center")
    val_table.add_column("Verification Status", justify="center")

    passed_count = 0
    for patch, vr in zip(patches, val_results):
        v_status = "[green bold]✓ VERIFIED[/green bold]" if vr.overall_status.value == "PASSED" else "[red bold]✗ FAILED[/red bold]"
        if vr.overall_status.value == "PASSED":
            passed_count += 1
        syn_icon = "✓" if vr.syntax_check else "✗"
        test_str = f"{vr.tests_passed_before}P/{vr.tests_failed_before}F -> {vr.tests_passed_after}P/{vr.tests_failed_after}F"
        val_table.add_row(patch.issue_id, patch.file_path, syn_icon, test_str, v_status)

    console.print(val_table)
    console.print()

    # Show diff sample
    if patches:
        console.print("[bold yellow]Sample Unified Patch Diff:[/bold yellow]")
        syntax = Syntax(patches[0].diff, "diff", theme="monokai", line_numbers=True)
        console.print(syntax)

    if apply_fixes and not fetcher.is_url:
        console.print("\n[bold green]Applying verified patches directly to local repository...[/bold green]")
        for patch in patches:
            target_path = fetcher.repo_path / patch.file_path
            apply_patch_to_file(target_path, patch.replacement_code)
            console.print(f"  [green]✓ Repaired: {patch.file_path}[/green]")

        # Record timeline update
        store = HealthTimelineStore()
        # Re-scan to get new score
        re_fetcher = RepositoryFetcher(str(fetcher.repo_path))
        re_fetcher.fetch()
        new_diag = DiagnosisEngine(re_fetcher).run_full_diagnosis()
        store.record_snapshot(
            repo_identifier=new_diag.repo_name,
            overall_score=new_diag.scorecard.overall_score,
            category_scores=new_diag.scorecard.category_scores,
            total_issues=new_diag.scorecard.total_issues,
            fixes_applied=len(patches),
            description=f"Auto-applied {len(patches)} verified patches"
        )
        console.print(f"\n[bold green]✓ Repository health improved from {diagnosis.scorecard.overall_score} -> {new_diag.scorecard.overall_score}![/bold green]")
    elif not apply_fixes:
        console.print("\n[dim]Run with '--apply' to write verified patches to disk automatically.[/dim]")


def report_command(target: str, output_file: str = "REPO_DOCTOR_REPORT.md"):
    fetcher = RepositoryFetcher(target)
    fetcher.fetch()
    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    # Generate patches and validate
    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)
    validator = PatchValidator(fetcher.repo_path)
    diagnosis.patches = patches
    diagnosis.validation_results = validator.validate_all_patches(patches)

    rep_gen = ReportGenerator(diagnosis)
    md = rep_gen.generate_markdown()

    out_path = Path(output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    console.print(f"[green]✓ Recruiter-ready engineering report generated at: [bold]{out_path.resolve()}[/bold][/green]")


def main():
    parser = argparse.ArgumentParser(description="RepoDoctor AI 🩺 Autonomous Repository Diagnostic & Repair Engineer")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    scan_p = subparsers.add_parser("scan", help="Scan and score repository")
    scan_p.add_argument("target", help="Repository path or GitHub URL")

    fix_p = subparsers.add_parser("fix", help="Diagnose, patch, and self-validate repository")
    fix_p.add_argument("target", help="Repository path or GitHub URL")
    fix_p.add_argument("--apply", action="store_true", help="Apply verified patches to disk")

    rep_p = subparsers.add_parser("report", help="Generate executive markdown/HTML engineering report")
    rep_p.add_argument("target", help="Repository path or GitHub URL")
    rep_p.add_argument("--output", default="REPO_DOCTOR_REPORT.md", help="Output file path")

    args = parser.parse_args()
    if args.command == "scan":
        scan_command(args.target)
    elif args.command == "fix":
        fix_command(args.target, apply_fixes=args.apply)
    elif args.command == "report":
        report_command(args.target, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
