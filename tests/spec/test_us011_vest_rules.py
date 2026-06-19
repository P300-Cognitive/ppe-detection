"""US-011 — specs/features/epic-05-rules.md"""

from __future__ import annotations

import pytest

from ppe_detection.domain.models import FrameDetections
from ppe_detection.rules.safety import SafetyRulesEngine


@pytest.mark.spec("US-011")
class TestUS011VestRules:
    def test_alert_when_vest_missing(self, app_config, person_bbox, ppe_bbox):
        app_config.rules.required_ppe = ["vest"]
        app_config.rules.confirmation_frames = 2
        engine = SafetyRulesEngine(app_config)

        person = person_bbox()
        helmet_only = FrameDetections(
            persons=[person],
            ppe_items=[ppe_bbox(130, 105, 170, 145, "Hardhat")],
        )

        engine.evaluate(helmet_only)
        result = engine.evaluate(helmet_only)
        assert result[0].alert is True
        assert "Colete" in result[0].alert_reason
