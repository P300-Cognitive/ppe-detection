"""US-014 — specs/features/epic-06-alerts.md"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ppe_detection.visualization.renderer import EvidenceStore, save_evidence


@pytest.mark.spec("US-014")
class TestUS014Evidence:
    def test_ac_014_1_saves_jpeg_with_timestamp(self, tmp_path: Path):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        path = save_evidence(frame, tmp_path, track_id=42, reason="Sem EPI: Capacete")

        assert path.exists()
        assert path.suffix == ".jpg"
        assert "alert_42_" in path.name

    def test_evidence_store_implements_port(self, tmp_path: Path):
        store = EvidenceStore()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        path = store.save(frame, tmp_path, 1, "test")
        assert path.exists()
