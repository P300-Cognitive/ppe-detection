"""US-022 — specs/manifest.yaml"""

from __future__ import annotations

import pytest

from ppe_detection.config import AppConfig, ModelConfig


@pytest.mark.spec("US-022")
class TestUS022Confidence:
    def test_confidence_configurable(self):
        config = AppConfig(model=ModelConfig(confidence=0.75))
        assert config.model.confidence == 0.75

    def test_confidence_in_valid_range(self):
        config = AppConfig(model=ModelConfig(confidence=0.45))
        assert 0.0 <= config.model.confidence <= 1.0
