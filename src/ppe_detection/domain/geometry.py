"""Geometria de associação — spec: specs/contracts/association.yaml."""

from __future__ import annotations

from ppe_detection.domain.models import BoundingBox


def iou(a: BoundingBox, b: BoundingBox) -> float:
    x_left = max(a.x1, b.x1)
    y_top = max(a.y1, b.y1)
    x_right = min(a.x2, b.x2)
    y_bottom = min(a.y2, b.y2)

    if x_right <= x_left or y_bottom <= y_top:
        return 0.0

    inter = (x_right - x_left) * (y_bottom - y_top)
    union = a.width * a.height + b.width * b.height - inter
    return inter / union if union > 0 else 0.0


def center_inside(inner: BoundingBox, outer: BoundingBox) -> bool:
    cx, cy = inner.center
    return outer.x1 <= cx <= outer.x2 and outer.y1 <= cy <= outer.y2
