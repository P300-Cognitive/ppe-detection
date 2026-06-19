"""Persistência de ocorrências — spec: specs/contracts/storage.yaml."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class OccurrenceRecord:
    id: int | None
    camera_id: str
    track_id: int
    reason: str
    missing_ppe: list[str]
    created_at: datetime
    image_path: str | None = None
    video_path: str | None = None


class OccurrenceStore:
    """Implementa OccurrenceStorePort — US-018."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS occurrences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    missing_ppe TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    image_path TEXT,
                    video_path TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_occ_created ON occurrences(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_occ_camera ON occurrences(camera_id)"
            )

    def record(self, occurrence: OccurrenceRecord) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO occurrences
                    (camera_id, track_id, reason, missing_ppe, created_at, image_path, video_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    occurrence.camera_id,
                    occurrence.track_id,
                    occurrence.reason,
                    json.dumps(occurrence.missing_ppe),
                    occurrence.created_at.isoformat(),
                    occurrence.image_path,
                    occurrence.video_path,
                ),
            )
            return int(cur.lastrowid)

    def update_video_path(self, occurrence_id: int, video_path: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE occurrences SET video_path = ? WHERE id = ?",
                (video_path, occurrence_id),
            )

    def search(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        camera_id: str | None = None,
        ppe_type: str | None = None,
        limit: int = 100,
    ) -> list[OccurrenceRecord]:
        query = "SELECT * FROM occurrences WHERE 1=1"
        params: list = []

        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date.isoformat())
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date.isoformat())
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        results = [self._row_to_record(row) for row in rows]

        if ppe_type:
            results = [r for r in results if ppe_type in r.missing_ppe]

        return results

    def count_by_period(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        camera_id: str | None = None,
    ) -> dict:
        occurrences = self.search(
            from_date=from_date, to_date=to_date, camera_id=camera_id, limit=10_000
        )
        total = len(occurrences)
        by_ppe: dict[str, int] = {}
        by_camera: dict[str, int] = {}

        for occ in occurrences:
            by_camera[occ.camera_id] = by_camera.get(occ.camera_id, 0) + 1
            for ppe in occ.missing_ppe:
                by_ppe[ppe] = by_ppe.get(ppe, 0) + 1

        base = max(total, 1)
        compliance_rate = max(0.0, 1.0 - (total / (total + base)))

        return {
            "total_infractions": total,
            "compliance_rate": round(compliance_rate, 4),
            "by_ppe_type": by_ppe,
            "by_camera": by_camera,
        }

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> OccurrenceRecord:
        return OccurrenceRecord(
            id=row["id"],
            camera_id=row["camera_id"],
            track_id=row["track_id"],
            reason=row["reason"],
            missing_ppe=json.loads(row["missing_ppe"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            image_path=row["image_path"],
            video_path=row["video_path"],
        )
