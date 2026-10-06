"""
RepoDoctor AI - Core Data Models and Schemas
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    ARCHITECTURE = "Architecture"
    CODE_QUALITY = "Code Quality"
    TESTING = "Testing"
    ML_ENGINEERING = "ML Engineering"
    SECURITY = "Security"
    DOCUMENTATION = "Documentation"
    REPRODUCIBILITY = "Reproducibility"
    CI_CD = "CI/CD"


class Issue(BaseModel):
    id: str = Field(..., description="Unique issue identifier")
    category: Category = Field(..., description="Category of the finding")
    title: str = Field(..., description="Short descriptive title")
    severity: Severity = Field(..., description="Risk severity level")
    file_path: str = Field(..., description="Relative file path where issue was found")
    line_number: int | None = Field(None, description="Starting line number")
    end_line_number: int | None = Field(None, description="Ending line number")
    code_snippet: str | None = Field(None, description="Current problematic code snippet")
    risk_explanation: str = Field(..., description="Why this is a risk / anti-pattern")
    recommendation: str = Field(..., description="Recommended fix or best practice")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    auto_fixable: bool = Field(default=True, description="Whether automated patch generation is available")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Patch(BaseModel):
    issue_id: str
    file_path: str
    description: str
    original_code: str
    replacement_code: str
    diff: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class ValidationStep(BaseModel):
    name: str
    status: ValidationStatus
    details: str
    execution_time_ms: float = 0.0


class ValidationResult(BaseModel):
    patch_id: str
    file_path: str
    overall_status: ValidationStatus
    syntax_check: bool = True
    import_check: bool = True
    tests_passed_before: int = 0
    tests_failed_before: int = 0
    tests_passed_after: int = 0
    tests_failed_after: int = 0
    test_output: str = ""
    steps: list[ValidationStep] = Field(default_factory=list)
    confidence: float = 0.95


class CategoryScore(BaseModel):
    category: Category
    score: float = Field(..., ge=0.0, le=10.0)
    issue_count: int = 0
    critical_count: int = 0
    summary: str = ""


class RepositoryScorecard(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=10.0)
    category_scores: dict[str, float] = Field(default_factory=dict)
    breakdown: list[CategoryScore] = Field(default_factory=list)
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    grade: str = "B"


class TimelineEntry(BaseModel):
    version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    overall_score: float
    category_scores: dict[str, float]
    total_issues: int
    fixes_applied: int
    description: str


class RepositoryDiagnosis(BaseModel):
    repo_name: str
    repo_path: str
    scan_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_files: int = 0
    python_files: int = 0
    total_loc: int = 0
    scorecard: RepositoryScorecard
    issues: list[Issue] = Field(default_factory=list)
    patches: list[Patch] = Field(default_factory=list)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    health_timeline: list[TimelineEntry] = Field(default_factory=list)
    executive_summary: str = ""
