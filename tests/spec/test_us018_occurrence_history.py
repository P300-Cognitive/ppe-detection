"""US-018 — specs/features/epic-07-dashboard.md"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ppe_detection.storage.occurrence_store import OccurrenceRecord, OccurrenceStore


@pytest.mark.spec("US-018")
class TestUS018OccurrenceHistory:
    @pytest.fixture
    def store(self, tmp_path):
        return OccurrenceStore(tmp_path / "test.db")

    def _record(self, store, camera_id, missing_ppe, days_ago=0):
        store.record(OccurrenceRecord(
            id=None,
            camera_id=camera_id,
            track_id=1,
            reason=f"Sem EPI: {missing_ppe[0]}",
            missing_ppe=missing_ppe,
            created_at=datetime.now() - timedelta(days=days_ago),
        ))

    def test_ac_018_1_filter_by_date(self, store):
        self._record(store, "cam1", ["helmet"], days_ago=10)
        self._record(store, "cam1", ["vest"], days_ago=0)
        recent = store.search(from_date=datetime.now() - timedelta(days=1))
        assert len(recent) == 1

    def test_ac_018_2_filter_by_camera(self, store):
        self._record(store, "cam1", ["helmet"])
        self._record(store, "cam2", ["vest"])
        result = store.search(camera_id="cam1")
        assert all(r.camera_id == "cam1" for r in result)

    def test_ac_018_3_filter_by_ppe_type(self, store):
        self._record(store, "cam1", ["helmet"])
        self._record(store, "cam1", ["vest"])
        result = store.search(ppe_type="helmet")
        assert all("helmet" in r.missing_ppe for r in result)
