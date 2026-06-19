"""Modelos de domínio — spec: specs/contracts/detector.yaml, rules.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    confidence: float
    track_id: int | None = None

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def head_region(self) -> BoundingBox:
        h = self.height * 0.25
        return BoundingBox(
            x1=self.x1, y1=self.y1, x2=self.x2, y2=self.y1 + h,
            label="_head", confidence=1.0,
        )

    def torso_region(self) -> BoundingBox:
        top = self.y1 + self.height * 0.20
        bottom = self.y1 + self.height * 0.65
        return BoundingBox(
            x1=self.x1, y1=top, x2=self.x2, y2=bottom,
            label="_torso", confidence=1.0,
        )


@dataclass
class FrameDetections:
    persons: list[BoundingBox] = field(default_factory=list)
    ppe_items: list[BoundingBox] = field(default_factory=list)
    violations: list[BoundingBox] = field(default_factory=list)


@dataclass
class PersonCompliance:
    track_id: int
    bbox: BoundingBox
    ppe_present: dict[str, bool] = field(default_factory=dict)
    missing_ppe: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    alert: bool = False
    alert_reason: str = ""
