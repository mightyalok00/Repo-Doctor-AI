"""
RepoDoctor AI - FastAPI Backend Server
Provides RESTful APIs for autonomous repository scanning, diagnosis, repair, and verification.
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from src.core.fetcher import RepositoryFetcher
from src.ai.diagnosis import DiagnosisEngine
from src.ai.patch_generator import PatchGenerator
from src.sandbox.validator import PatchValidator
from src.core.history_store import HealthTimelineStore
from src.report.generator import ReportGenerator
from src.core.models import RepositoryDiagnosis, TimelineEntry
from src.core.git_utils import apply_patch_to_file

app = FastAPI(
    title="RepoDoctor AI API 🩺",
    version="1.0.0",
    description="Autonomous AI-powered engineer that diagnoses, scores, and repairs GitHub repositories."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

history_store = HealthTimelineStore()


class ScanRequest(BaseModel):
    target: str = Field(..., description="Local directory path or GitHub URL")


class ApplyPatchRequest(BaseModel):
    target: str
    patch_ids: Optional[List[str]] = None


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "RepoDoctor AI",
        "version": "1.0.0",
        "tagline": "An AI-powered autonomous engineer that diagnoses, scores, and repairs GitHub repositories."
    }


@app.post("/api/scan", response_model=RepositoryDiagnosis)
def scan_repository(req: ScanRequest):
    """Scan and diagnose a repository, computing multi-dimensional scorecard."""
    fetcher = RepositoryFetcher(req.target)
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
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        fetcher.cleanup()


@app.post("/api/repair", response_model=Dict[str, Any])
def repair_and_validate(req: ScanRequest):
    """Diagnose, generate candidate patches, and self-validate them in sandbox."""
    fetcher = RepositoryFetcher(req.target)
    try:
        fetcher.fetch()
        engine = DiagnosisEngine(fetcher)
        diagnosis = engine.run_full_diagnosis()

        patch_gen = PatchGenerator(fetcher)
        patches = patch_gen.generate_all_patches(diagnosis.issues)

        validator = PatchValidator(fetcher.repo_path)
        val_results = validator.validate_all_patches(patches)

        return {
            "repo_name": diagnosis.repo_name,
            "baseline_score": diagnosis.scorecard.overall_score,
            "total_issues": len(diagnosis.issues),
            "patches": [p.model_dump() for p in patches],
            "validation_results": [vr.model_dump() for vr in val_results]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        fetcher.cleanup()


@app.post("/api/apply-fixes")
def apply_fixes(req: ApplyPatchRequest):
    """Apply verified patches directly to target repository."""
    fetcher = RepositoryFetcher(req.target)
    if fetcher.is_url:
        raise HTTPException(status_code=400, detail="Cannot apply fixes directly to remote URL without cloning")

    fetcher.fetch()
    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)

    applied_files = []
    for patch in patches:
        if req.patch_ids is None or patch.issue_id in req.patch_ids:
            target_file = fetcher.repo_path / patch.file_path
            if apply_patch_to_file(target_file, patch.replacement_code):
                applied_files.append(patch.file_path)

    # Re-evaluate
    re_fetcher = RepositoryFetcher(req.target)
    re_fetcher.fetch()
    re_engine = DiagnosisEngine(re_fetcher)
    new_diagnosis = re_engine.run_full_diagnosis()

    history_store.record_snapshot(
        repo_identifier=diagnosis.repo_name,
        overall_score=new_diagnosis.scorecard.overall_score,
        category_scores=new_diagnosis.scorecard.category_scores,
        total_issues=new_diagnosis.scorecard.total_issues,
        fixes_applied=len(applied_files),
        description=f"Auto-applied {len(applied_files)} verified patches"
    )

    return {
        "status": "success",
        "applied_count": len(applied_files),
        "applied_files": applied_files,
        "score_before": diagnosis.scorecard.overall_score,
        "score_after": new_diagnosis.scorecard.overall_score,
        "issues_before": len(diagnosis.issues),
        "issues_after": len(new_diagnosis.issues)
    }


@app.get("/api/timeline/{repo_name}", response_model=List[TimelineEntry])
def get_timeline(repo_name: str):
    """Retrieve historical health timeline entries for repository."""
    return history_store.get_timeline(repo_name)


@app.post("/api/report")
def generate_report(req: ScanRequest, format: str = "markdown"):
    """Generate Markdown or HTML engineering report."""
    fetcher = RepositoryFetcher(req.target)
    fetcher.fetch()
    engine = DiagnosisEngine(fetcher)
    diagnosis = engine.run_full_diagnosis()

    patch_gen = PatchGenerator(fetcher)
    patches = patch_gen.generate_all_patches(diagnosis.issues)
    validator = PatchValidator(fetcher.repo_path)
    diagnosis.patches = patches
    diagnosis.validation_results = validator.validate_all_patches(patches)

    rep_gen = ReportGenerator(diagnosis)
    if format.lower() == "html":
        return {"html": rep_gen.generate_html()}
    return {"markdown": rep_gen.generate_markdown()}
