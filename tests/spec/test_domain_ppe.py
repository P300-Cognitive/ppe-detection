"""Testes do domínio PPE."""

from __future__ import annotations

import pytest

from ppe_detection.config import ClassConfig
from ppe_detection.domain.models import FrameDetections
from ppe_detection.domain.ppe import (
    count_people,
    relevant_violations,
    violation_to_ppe_key,
)


@pytest.mark.spec("US-018")
class TestDomainPPE:
    def test_violation_to_ppe_key(self):
        assert violation_to_ppe_key("NO-Hardhat") == "helmet"
        assert violation_to_ppe_key("NO-Safety Vest") == "vest"

    def test_relevant_violations_filters_by_required(self, person_bbox, ppe_bbox):
        classes = ClassConfig()
        no_helmet = person_bbox()
        no_helmet.label = "NO-Hardhat"
        no_vest = person_bbox()
        no_vest.label = "NO-Safety Vest"

        detections = FrameDetections(violations=[no_helmet, no_vest])
        result = relevant_violations(detections, ["helmet"], classes)
        assert len(result) == 1
        assert result[0].label == "NO-Hardhat"

    def test_count_people_from_violations_deduplicates(self, person_bbox):
        classes = ClassConfig()
        v1 = person_bbox()
        v1.label = "NO-Hardhat"
        v2 = person_bbox()
        v2.label = "NO-Mask"
        # Mesma região → mesma pessoa
        detections = FrameDetections(violations=[v1, v2])
        assert count_people(detections, ["helmet", "mask"], classes) == 1

    def test_count_people_from_persons(self, person_bbox):
        classes = ClassConfig()
        detections = FrameDetections(persons=[person_bbox(), person_bbox(track_id=2)])
        assert count_people(detections, ["helmet"], classes) == 2
