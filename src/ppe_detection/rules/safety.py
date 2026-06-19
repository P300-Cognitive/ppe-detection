from __future__ import annotations

from ppe_detection.association.matcher import PPEAssociator, create_associator
from ppe_detection.config import AppConfig
from ppe_detection.domain.models import BoundingBox, FrameDetections, PersonCompliance


class SafetyRulesEngine:
    """Implementa RulesEnginePort — specs/contracts/rules.yaml."""

    def __init__(self, config: AppConfig, associator: PPEAssociator | None = None) -> None:
        self._config = config
        self._associator = associator or create_associator(config)
        self._violation_counters: dict[tuple[int, str], int] = {}

    def evaluate(self, detections: FrameDetections) -> list[PersonCompliance]:
        results: list[PersonCompliance] = []

        for person in detections.persons:
            track_id = person.track_id if person.track_id is not None else id(person)
            compliance = PersonCompliance(track_id=track_id, bbox=person)

            for ppe_type in self._config.rules.required_ppe:
                associated = self._associator.associate(
                    person, detections.ppe_items, ppe_type
                )
                has_ppe = len(associated) > 0
                compliance.ppe_present[ppe_type] = has_ppe
                if not has_ppe:
                    compliance.missing_ppe.append(ppe_type)

            for violation in detections.violations:
                ppe_key = self._violation_type(violation.label)
                if ppe_key and self._violation_near_person(violation, person):
                    compliance.violations.append(violation.label)
                    normalized = ppe_key.replace("no_", "")
                    if normalized not in compliance.missing_ppe:
                        compliance.missing_ppe.append(normalized)

            if compliance.missing_ppe:
                if self._confirm_violation(track_id, compliance.missing_ppe):
                    compliance.alert = True
                    labels = ", ".join(self._ppe_label(p) for p in compliance.missing_ppe)
                    compliance.alert_reason = f"Sem EPI: {labels}"
            else:
                self._reset_counters(track_id)

            results.append(compliance)

        return results

    def _confirm_violation(self, track_id: int, missing: list[str]) -> bool:
        threshold = self._config.rules.confirmation_frames
        for ppe in missing:
            key = (track_id, ppe)
            self._violation_counters[key] = self._violation_counters.get(key, 0) + 1
            if self._violation_counters[key] < threshold:
                return False
        return True

    def _reset_counters(self, track_id: int) -> None:
        keys = [k for k in self._violation_counters if k[0] == track_id]
        for key in keys:
            del self._violation_counters[key]

    @staticmethod
    def _violation_near_person(violation: BoundingBox, person: BoundingBox) -> bool:
        cx, cy = violation.center
        return person.x1 <= cx <= person.x2 and person.y1 <= cy <= person.y2

    def _violation_type(self, label: str) -> str | None:
        for ppe_key, labels in self._config.classes.violation.items():
            if label in labels:
                return ppe_key.replace("no_", "")
        if label.startswith("NO-"):
            return label.replace("NO-", "").lower().replace(" ", "_").replace("-", "_")
        return None

    @staticmethod
    def _ppe_label(ppe_type: str) -> str:
        labels = {
            "helmet": "Capacete",
            "vest": "Colete",
            "gloves": "Luvas",
            "goggles": "Óculos",
            "mask": "Máscara",
            "boots": "Botas",
        }
        return labels.get(ppe_type, ppe_type)
