"""US-008 — specs/features/epic-04-association.md"""

from __future__ import annotations

import pytest

from ppe_detection.association.matcher import PPEAssociator
from ppe_detection.config import ClassConfig
from ppe_detection.contracts.ports import PPEAssociatorPort


@pytest.mark.spec("US-008")
class TestUS008HelmetAssociation:
    @pytest.fixture
    def associator(self) -> PPEAssociator:
        return PPEAssociator(ClassConfig(helmet=["Hardhat"]))

    def test_ac_008_1_helmet_on_head_associates(self, associator, person_bbox, ppe_bbox):
        person = person_bbox()
        helmet = ppe_bbox(130, 105, 170, 145, "Hardhat")
        result = associator.associate(person, [helmet], "helmet")
        assert len(result) == 1
        assert result[0].label == "Hardhat"

    def test_ac_008_2_distant_helmet_does_not_associate(self, associator, person_bbox, ppe_bbox):
        person = person_bbox()
        helmet = ppe_bbox(380, 105, 420, 145, "Hardhat")
        result = associator.associate(person, [helmet], "helmet")
        assert result == []

    def test_implements_associator_port(self, associator):
        assert isinstance(associator, PPEAssociatorPort)
