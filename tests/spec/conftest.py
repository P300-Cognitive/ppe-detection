from __future__ import annotations

import pytest

from ppe_detection.config import AppConfig, CameraConfig, ClassConfig, RulesConfig


@pytest.fixture
def default_classes() -> ClassConfig:
    return ClassConfig(
        helmet=["Hardhat"],
        vest=["Safety Vest"],
        gloves=["Gloves"],
        goggles=["Goggles"],
        mask=["Mask"],
    )


@pytest.fixture
def app_config(default_classes: ClassConfig) -> AppConfig:
    config = AppConfig()
    config.classes = default_classes
    config.rules = RulesConfig(required_ppe=["helmet", "vest"], confirmation_frames=3)
    return config


@pytest.fixture
def person_bbox():
    from ppe_detection.domain.models import BoundingBox

    def _factory(x1=100, y1=100, x2=200, y2=300, track_id=1):
        return BoundingBox(x1, y1, x2, y2, "Person", 0.9, track_id)

    return _factory


@pytest.fixture
def ppe_bbox():
    from ppe_detection.domain.models import BoundingBox

    def _factory(x1, y1, x2, y2, label, conf=0.85):
        return BoundingBox(x1, y1, x2, y2, label, conf)

    return _factory
