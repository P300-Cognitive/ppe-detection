from __future__ import annotations

import logging

from ppe_detection.association.matcher import PPEAssociator, create_associator
from ppe_detection.config import AppConfig
from ppe_detection.domain.models import BoundingBox, FrameDetections, PersonCompliance
from ppe_detection.domain.ppe import ppe_label, relevant_violations, violation_to_ppe_key

logger = logging.getLogger(__name__)


class SafetyRulesEngine:
    """Implementa RulesEnginePort — specs/contracts/rules.yaml."""

    def __init__(self, config: AppConfig, associator: PPEAssociator | None = None) -> None:
        self._config = config
        self._associator = associator or create_associator(config)
        self._violation_counters: dict[tuple[int, str], int] = {}

    def evaluate(self, detections: FrameDetections) -> list[PersonCompliance]:
        results: list[PersonCompliance] = []
        covered_violation_ids: set[int] = set()

        for person in detections.persons:
            compliance = self._evaluate_person(person, detections, covered_violation_ids)
            results.append(compliance)

        for i, violation in enumerate(
            relevant_violations(detections, self._config.rules.required_ppe, self._config.classes)
        ):
            if id(violation) in covered_violation_ids:
                continue
            compliance = self._evaluate_standalone_violation(violation, i)
            if compliance:
                results.append(compliance)

        return results

    def _evaluate_person(
        self,
        person: BoundingBox,
        detections: FrameDetections,
        covered_violation_ids: set[int],
    ) -> PersonCompliance:
        track_id = person.track_id if person.track_id is not None else id(person)
        compliance = PersonCompliance(track_id=track_id, bbox=person)

        for ppe_type in self._config.rules.required_ppe:
            associated = self._associator.associate(person, detections.ppe_items, ppe_type)
            has_ppe = bool(associated)
            compliance.ppe_present[ppe_type] = has_ppe
            if not has_ppe:
                compliance.missing_ppe.append(ppe_type)

        for violation in relevant_violations(
            detections, self._config.rules.required_ppe, self._config.classes,
        ):
            ppe_key = violation_to_ppe_key(violation.label, self._config.classes)
            if not ppe_key or not self._violation_near_person(violation, person):
                continue
            covered_violation_ids.add(id(violation))
            compliance.violations.append(violation.label)
            if ppe_key not in compliance.missing_ppe:
                compliance.missing_ppe.append(ppe_key)

        self._apply_confirmation(compliance, track_id)
        return compliance

    def _evaluate_standalone_violation(
        self, violation: BoundingBox, index: int,
    ) -> PersonCompliance | None:
        ppe_key = violation_to_ppe_key(violation.label, self._config.classes)
        if not ppe_key or ppe_key not in self._config.rules.required_ppe:
            return None

        track_id = violation.track_id if violation.track_id is not None else -(index + 1)
        compliance = PersonCompliance(
            track_id=track_id,
            bbox=violation,
            ppe_present={ppe_key: False},
            missing_ppe=[ppe_key],
            violations=[violation.label],
        )
        self._apply_confirmation(compliance, track_id)
        return compliance

    def _apply_confirmation(self, compliance: PersonCompliance, track_id: int) -> None:
        if not compliance.missing_ppe:
            self._reset_counters(track_id)
            return

        if self._confirm_violation(track_id, compliance.missing_ppe):
            compliance.alert = True
            labels = ", ".join(ppe_label(p) for p in compliance.missing_ppe)
            compliance.alert_reason = f"Sem EPI: {labels}"
        else:
            compliance.alert = False
            compliance.alert_reason = ""

    def _confirm_violation(self, track_id: int, missing: list[str]) -> bool:
        threshold = self._config.rules.confirmation_frames
        for ppe in missing:
            key = (track_id, ppe)
            self._violation_counters[key] = self._violation_counters.get(key, 0) + 1
            if self._violation_counters[key] < threshold:
                return False
        return True

    def _reset_counters(self, track_id: int) -> None:
        for key in [k for k in self._violation_counters if k[0] == track_id]:
            del self._violation_counters[key]

    @staticmethod
    def _violation_near_person(violation: BoundingBox, person: BoundingBox) -> bool:
        cx, cy = violation.center
        return person.x1 <= cx <= person.x2 and person.y1 <= cy <= person.y2
