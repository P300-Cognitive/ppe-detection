"""US-012 — specs/features/epic-05-rules.md"""

from __future__ import annotations

import pytest

from ppe_detection.config import load_config
from ppe_detection.domain.models import FrameDetections
from ppe_detection.rules.safety import SafetyRulesEngine


@pytest.mark.spec("US-012")
class TestUS012ConfigurableRules:
    def test_ac_012_1_only_configured_ppe_required(self, app_config, person_bbox, ppe_bbox):
        app_config.rules.required_ppe = ["helmet"]
        app_config.rules.confirmation_frames = 1
        engine = SafetyRulesEngine(app_config)

        person = person_bbox()
        with_helmet = FrameDetections(
            persons=[person],
            ppe_items=[ppe_bbox(130, 105, 170, 145, "Hardhat")],
        )
        result = engine.evaluate(with_helmet)
        assert result[0].alert is False

    def test_default_config_loads_required_ppe(self):
        config = load_config()
        assert "helmet" in config.rules.required_ppe
