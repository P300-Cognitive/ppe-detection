"""US-010 — specs/features/epic-05-rules.md"""

from __future__ import annotations

import pytest

from ppe_detection.domain.models import FrameDetections
from ppe_detection.rules.safety import SafetyRulesEngine


@pytest.mark.spec("US-010")
class TestUS010HelmetRules:
    def test_ac_010_1_alert_after_confirmation(self, app_config, person_bbox):
        app_config.rules.required_ppe = ["helmet"]
        app_config.rules.confirmation_frames = 3
        engine = SafetyRulesEngine(app_config)
        detections = FrameDetections(persons=[person_bbox()])

        for i in range(2):
            result = engine.evaluate(detections)
            assert result[0].alert is False, f"Frame {i+1} não deve alertar"

        result = engine.evaluate(detections)
        assert result[0].alert is True
        assert "Capacete" in result[0].alert_reason

    def test_ac_010_2_no_alert_before_threshold(self, app_config, person_bbox):
        app_config.rules.required_ppe = ["helmet"]
        app_config.rules.confirmation_frames = 5
        engine = SafetyRulesEngine(app_config)
        detections = FrameDetections(persons=[person_bbox()])

        for _ in range(2):
            result = engine.evaluate(detections)
            assert result[0].alert is False
