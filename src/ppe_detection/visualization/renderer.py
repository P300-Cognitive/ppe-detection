from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from ppe_detection.config import AppConfig
from ppe_detection.domain.models import BoundingBox, FrameDetections, PersonCompliance
from ppe_detection.domain.ppe import (
    count_people,
    relevant_ppe_items,
    relevant_violations,
)


class FrameRenderer:
    """Implementa RendererPort — specs/contracts/renderer.yaml."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def render(
        self,
        frame: np.ndarray,
        detections: FrameDetections,
        compliance: list[PersonCompliance],
        fps: float = 0.0,
    ) -> np.ndarray:
        output = frame.copy()
        alert_ids = {c.track_id for c in compliance if c.alert}
        required = self._config.rules.required_ppe
        classes = self._config.classes

        for person in detections.persons:
            is_alert = person.track_id in alert_ids
            color = (
                self._config.display.alert_color if is_alert
                else self._config.display.person_color
            )
            self._draw_box(output, person, color, person.track_id)

        for item in relevant_ppe_items(detections, required, classes):
            self._draw_box(output, item, self._config.display.ppe_color)

        drawn_tracks = {p.track_id for p in detections.persons if p.track_id is not None}
        for violation in relevant_violations(detections, required, classes):
            if violation.track_id not in drawn_tracks:
                self._draw_box(output, violation, self._config.display.alert_color)

        for person_comp in compliance:
            if person_comp.alert:
                self._draw_alert_banner(output, person_comp)

        self._draw_hud(output, fps, detections, compliance)
        return output

    def _draw_box(
        self,
        frame: np.ndarray,
        bbox: BoundingBox,
        color: tuple[int, int, int],
        track_id: int | None = None,
    ) -> None:
        x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = bbox.label
        if track_id is not None:
            label = f"#{track_id} {label}"
        if self._config.display.show_confidence:
            label = f"{label} {bbox.confidence:.0%}"

        self._draw_label(frame, label, x1, y1, color)

    def _draw_label(
        self,
        frame: np.ndarray,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale, thickness = 0.5, 1
        (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
        cv2.rectangle(frame, (x, y - th - 8), (x + tw + 4, y), color, -1)
        cv2.putText(frame, text, (x + 2, y - 4), font, scale, (255, 255, 255), thickness)

    def _draw_alert_banner(self, frame: np.ndarray, person: PersonCompliance) -> None:
        x1, y1, x2, y2 = (
            int(person.bbox.x1), int(person.bbox.y1),
            int(person.bbox.x2), int(person.bbox.y2),
        )
        cv2.rectangle(frame, (x1, y1), (x2, y2), self._config.display.alert_color, 4)

        alert_text = f"ALERTA #{person.track_id}: {person.alert_reason}"
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, h - 40), (w, h), self._config.display.alert_color, -1)
        cv2.putText(
            frame, alert_text, (10, h - 14),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2,
        )

    def _draw_hud(
        self,
        frame: np.ndarray,
        fps: float,
        detections: FrameDetections,
        compliance: list[PersonCompliance],
    ) -> None:
        n_people = count_people(
            detections, self._config.rules.required_ppe, self._config.classes,
        )
        alerts = sum(1 for c in compliance if c.alert)
        text = f"FPS: {fps:.1f} | Pessoas: {n_people} | Alertas: {alerts}"
        cv2.putText(frame, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)


class EvidenceStore:
    """Implementa EvidencePort — specs/contracts/renderer.yaml."""

    def save(
        self,
        frame: np.ndarray,
        output_dir: Path,
        track_id: int,
        reason: str,
    ) -> Path:
        return save_evidence(frame, output_dir, track_id, reason)


def save_evidence(
    frame: np.ndarray,
    output_dir: Path,
    track_id: int,
    reason: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"alert_{track_id}_{timestamp}.jpg"

    annotated = frame.copy()
    cv2.putText(
        annotated, f"{timestamp} - {reason}",
        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
    )
    cv2.imwrite(str(path), annotated)
    return path
