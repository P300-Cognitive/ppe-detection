"""Associação de EPIs detectados às pessoas correspondentes por IoU de região corporal."""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from src.core.models import BBox


def _iou(a: BBox, b: BBox) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    if inter == 0:
        return 0.0
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _head_region(bbox: BBox) -> BBox:
    """Terço superior da bounding box — região da cabeça."""
    x1, y1, x2, y2 = bbox
    return (x1, y1, x2, y1 + int((y2 - y1) * 0.30))


def _torso_region(bbox: BBox) -> BBox:
    """Faixa central da bounding box — região do tronco."""
    x1, y1, x2, y2 = bbox
    h = y2 - y1
    return (x1, y1 + int(h * 0.20), x2, y1 + int(h * 0.70))


class PPEAssociator:
    """Associa cada EPI detectado à pessoa mais próxima via IoU de região corporal.

    Retorna Dict[person_id → lista de class_name de EPIs associados].
    EPIs sem correspondência suficiente (< IOU_THRESHOLD) não são associados.
    """

    IOU_THRESHOLD = 0.10

    _REGION: Dict[str, Callable[[BBox], BBox]] = {
        "helmet": _head_region,
        "vest":   _torso_region,
    }

    def associate(
        self,
        persons: List[Any],
        ppe_detections: List[Any],
    ) -> Dict[int, List[str]]:
        result: Dict[int, List[str]] = {p.track_id: [] for p in persons}

        for ppe in ppe_detections:
            region_fn = self._REGION.get(ppe.class_name)
            best_id: int | None = None
            best_score = self.IOU_THRESHOLD

            for person in persons:
                region = region_fn(person.bbox) if region_fn else person.bbox
                score = _iou(region, ppe.bbox)
                if score > best_score:
                    best_score = score
                    best_id = person.track_id

            if best_id is not None:
                result[best_id].append(ppe.class_name)

        return result
