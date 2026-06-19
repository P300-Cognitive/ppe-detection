"""US-013 — specs/features/epic-06-alerts.md"""

from __future__ import annotations

import numpy as np
import pytest

from ppe_detection.config import AppConfig
from ppe_detection.domain.models import FrameDetections, PersonCompliance
from ppe_detection.visualization.renderer import FrameRenderer


@pytest.mark.spec("US-013")
class TestUS013VisualAlert:
    def test_ac_013_1_render_produces_output_frame(self, app_config, person_bbox):
        renderer = FrameRenderer(app_config)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        person = person_bbox()
        compliance = [
            PersonCompliance(
                track_id=1, bbox=person, alert=True, alert_reason="Sem EPI: Capacete"
            )
        ]
        result = renderer.render(frame, FrameDetections(persons=[person]), compliance)
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)
