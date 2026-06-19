"""US-009 — specs/features/epic-04-association.md"""

from __future__ import annotations

import pytest

from ppe_detection.association.matcher import PPEAssociator
from ppe_detection.config import ClassConfig


@pytest.mark.spec("US-009")
class TestUS009VestAssociation:
    @pytest.fixture
    def associator(self) -> PPEAssociator:
        return PPEAssociator(ClassConfig(vest=["Safety Vest"]))

    def test_ac_009_1_vest_on_torso_associates(self, associator, person_bbox, ppe_bbox):
        person = person_bbox()
        vest = ppe_bbox(120, 160, 180, 220, "Safety Vest")
        result = associator.associate(person, [vest], "vest")
        assert len(result) == 1

    def test_ac_009_2_vest_on_head_does_not_associate(self, associator, person_bbox, ppe_bbox):
        person = person_bbox()
        vest = ppe_bbox(130, 105, 170, 140, "Safety Vest")
        result = associator.associate(person, [vest], "vest")
        assert result == []
