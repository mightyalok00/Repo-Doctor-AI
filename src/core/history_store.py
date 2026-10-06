"""
RepoDoctor AI - Repository Health Timeline Store
"""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from src.core.models import TimelineEntry


class HealthTimelineStore:
    """Stores and retrieves repository health history over iterations (v1, v2, v3, ...)."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            # Default to local user home or cache dir
            base_dir = Path.home() / ".repodoctor"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "timeline.db"
        else:
            self.db_path = db_path
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repo_timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_identifier TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    category_scores_json TEXT NOT NULL,
                    total_issues INTEGER NOT NULL,
                    fixes_applied INTEGER NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            conn.commit()

    def record_snapshot(
        self,
        repo_identifier: str,
        overall_score: float,
        category_scores: Dict[str, float],
        total_issues: int,
        fixes_applied: int = 0,
        description: str = ""
    ) -> TimelineEntry:
        """Record a new snapshot and return the created TimelineEntry with auto-incrementing version."""
        history = self.get_timeline(repo_identifier)
        next_ver_num = len(history) + 1
        version_str = f"v{next_ver_num}"

        now_str = datetime.utcnow().isoformat()
        cat_json = json.dumps(category_scores)

        if not description:
            if next_ver_num == 1:
                description = "Initial scan & diagnosis"
            else:
                prev_score = history[-1].overall_score
                diff = overall_score - prev_score
                sign = "+" if diff >= 0 else ""
                description = f"Repaired {fixes_applied} issues (Score {sign}{diff:.1f})"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO repo_timeline 
                (repo_identifier, version, timestamp, overall_score, category_scores_json, total_issues, fixes_applied, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (repo_identifier, version_str, now_str, overall_score, cat_json, total_issues, fixes_applied, description))
            conn.commit()

        return TimelineEntry(
            version=version_str,
            timestamp=datetime.fromisoformat(now_str),
            overall_score=overall_score,
            category_scores=category_scores,
            total_issues=total_issues,
            fixes_applied=fixes_applied,
            description=description
        )

    def get_timeline(self, repo_identifier: str) -> List[TimelineEntry]:
        """Fetch all historical timeline entries for a repository."""
        entries: List[TimelineEntry] = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, timestamp, overall_score, category_scores_json, total_issues, fixes_applied, description
                FROM repo_timeline
                WHERE repo_identifier = ?
                ORDER BY id ASC
            """, (repo_identifier,))
            rows = cursor.fetchall()
            for r in rows:
                try:
                    cat_scores = json.loads(r[3])
                except Exception:
                    cat_scores = {}
                entries.append(
                    TimelineEntry(
                        version=r[0],
                        timestamp=datetime.fromisoformat(r[1]),
                        overall_score=r[2],
                        category_scores=cat_scores,
                        total_issues=r[4],
                        fixes_applied=r[5],
                        description=r[6]
                    )
                )
        return entries
