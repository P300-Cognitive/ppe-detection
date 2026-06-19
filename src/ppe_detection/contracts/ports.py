"""Ports (contratos) — derivados de specs/contracts/*.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, Protocol, runtime_checkable

import numpy as np

from ppe_detection.domain.models import BoundingBox, FrameDetections, PersonCompliance

Frame = np.ndarray


@runtime_checkable
class CameraPort(Protocol):
    """specs/contracts/camera.yaml"""

    def connect(self) -> None: ...
    def read(self) -> Frame | None: ...
    def frames(self) -> Iterator[Frame]: ...
    def release(self) -> None: ...


@runtime_checkable
class DetectorPort(Protocol):
    """specs/contracts/detector.yaml"""

    def detect(self, frame: Frame) -> FrameDetections: ...


@runtime_checkable
class PPEAssociatorPort(Protocol):
    """specs/contracts/association.yaml"""

    def associate(
        self,
        person: BoundingBox,
        ppe_items: list[BoundingBox],
        ppe_type: str,
    ) -> list[BoundingBox]: ...


@runtime_checkable
class RulesEnginePort(Protocol):
    """specs/contracts/rules.yaml"""

    def evaluate(self, detections: FrameDetections) -> list[PersonCompliance]: ...


@runtime_checkable
class RendererPort(Protocol):
    """specs/contracts/renderer.yaml"""

    def render(
        self,
        frame: Frame,
        detections: FrameDetections,
        compliance: list[PersonCompliance],
        fps: float = 0.0,
    ) -> Frame: ...


@runtime_checkable
class EvidencePort(Protocol):
    """specs/contracts/renderer.yaml — EvidencePort"""

    def save(
        self,
        frame: Frame,
        output_dir: Path,
        track_id: int,
        reason: str,
    ) -> Path: ...
