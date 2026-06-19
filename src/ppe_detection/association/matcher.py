"""Associação pessoa-EPI — spec: specs/features/epic-04-association.md."""

from __future__ import annotations

from ppe_detection.config import AppConfig, ClassConfig
from ppe_detection.domain.geometry import center_inside, iou
from ppe_detection.domain.models import BoundingBox


class PPEAssociator:
    """Implementa PPEAssociatorPort — specs/contracts/association.yaml."""

    def __init__(self, classes: ClassConfig) -> None:
        self._classes = classes

    def associate(
        self,
        person: BoundingBox,
        ppe_items: list[BoundingBox],
        ppe_type: str,
    ) -> list[BoundingBox]:
        allowed = set(self._labels_for(ppe_type))
        candidates = [p for p in ppe_items if p.label in allowed]

        region = self._region_for(person, ppe_type)
        matched: list[BoundingBox] = []
        for item in candidates:
            if center_inside(item, region) or iou(item, region) > 0.05:
                matched.append(item)
        return matched

    def _labels_for(self, ppe_type: str) -> list[str]:
        mapping = {
            "helmet": self._classes.helmet,
            "vest": self._classes.vest,
            "gloves": self._classes.gloves,
            "goggles": self._classes.goggles,
            "mask": self._classes.mask,
            "boots": self._classes.boots,
        }
        return mapping.get(ppe_type, [])

    @staticmethod
    def _region_for(person: BoundingBox, ppe_type: str) -> BoundingBox:
        if ppe_type == "helmet":
            return person.head_region()
        if ppe_type == "vest":
            return person.torso_region()
        return person


def create_associator(config: AppConfig) -> PPEAssociator:
    return PPEAssociator(config.classes)
