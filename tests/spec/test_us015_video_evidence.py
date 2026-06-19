"""US-015 — specs/features/epic-06-alerts.md"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ppe_detection.config import EvidenceConfig
from ppe_detection.evidence.video_buffer import VideoRingBuffer
from ppe_detection.evidence.video_store import VideoEvidenceStore


@pytest.mark.spec("US-015")
class TestUS015VideoEvidence:
    def test_ac_015_1_buffer_keeps_pre_alert_frames(self):
        buf = VideoRingBuffer(max_frames=5)
        frames = [np.zeros((10, 10, 3), dtype=np.uint8) for _ in range(5)]
        for f in frames:
            buf.push(f)
        snap = buf.snapshot()
        assert len(snap) == 5

    def test_ac_015_2_post_alert_frames_finalize_video(self, tmp_path: Path):
        config = EvidenceConfig(
            save_video=True,
            video_pre_seconds=0.1,
            video_post_seconds=0.2,
            video_fps=5,
        )
        store = VideoEvidenceStore(config)
        frame = np.zeros((48, 64, 3), dtype=np.uint8)

        with patch("cv2.VideoWriter") as mock_writer:
            mock_writer.return_value = MagicMock()
            store.on_alert(frame, tmp_path, track_id=1, reason="Sem EPI: Capacete")
            paths = []
            for _ in range(1):
                paths.extend(store.tick(frame, tmp_path))

        assert mock_writer.called
        assert len(paths) == 1
        assert paths[0].suffix == ".mp4"
