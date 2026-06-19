from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ppe_detection.config import AppConfig
from ppe_detection.detection.model_loader import resolve_model_path
from ppe_detection.domain.models import BoundingBox, FrameDetections

if TYPE_CHECKING:
    from ultralytics.engine.results import Results

logger = logging.getLogger(__name__)


class YOLODetector:
    """Implementa DetectorPort — specs/contracts/detector.yaml."""

    def __init__(self, config: AppConfig) -> None:
        from ultralytics import YOLO

        self._config = config
        model_path = resolve_model_path(config.model.path)
        self._model = YOLO(model_path)
        self._class_groups = self._build_class_groups()
        self._frame_count = 0

    def _build_class_groups(self) -> dict[str, set[int]]:
        names = self._model.names
        label_to_id = {v: k for k, v in names.items()}

        logger.info("Classes do modelo: %s", list(names.values()))

        groups: dict[str, set[int]] = {"person": set(), "ppe": set(), "violation": set()}

        self._map_labels(groups["person"], self._config.classes.person, label_to_id, "pessoa")
        ppe_labels = (
            self._config.classes.helmet + self._config.classes.vest
            + self._config.classes.gloves + self._config.classes.goggles
            + self._config.classes.mask + self._config.classes.boots
        )
        self._map_labels(groups["ppe"], ppe_labels, label_to_id, "EPI")

        violation_labels = [
            label for labels in self._config.classes.violation.values() for label in labels
        ]
        self._map_labels(groups["violation"], violation_labels, label_to_id, "violação")

        logger.info(
            "Grupos mapeados — pessoa: %s, EPI: %s, violação: %s",
            groups["person"], groups["ppe"], groups["violation"],
        )
        return groups

    @staticmethod
    def _map_labels(
        target: set[int],
        labels: list[str],
        label_to_id: dict[str, int],
        kind: str,
    ) -> None:
        for label in labels:
            if label in label_to_id:
                target.add(label_to_id[label])
            else:
                logger.warning("Classe %s '%s' não encontrada no modelo.", kind, label)

    def detect(self, frame: np.ndarray) -> FrameDetections:
        kwargs: dict = {"conf": self._config.model.confidence, "verbose": False}
        if self._config.model.device:
            kwargs["device"] = self._config.model.device

        if self._config.tracking.enabled:
            results = self._model.track(
                frame, persist=True,
                tracker=self._config.tracking.tracker, **kwargs,
            )
        else:
            results = self._model.predict(frame, **kwargs)

        detections = self._parse_results(results[0])
        self._log_periodic(detections)
        return detections

    def _log_periodic(self, detections: FrameDetections) -> None:
        self._frame_count += 1
        if self._frame_count % 30 != 0:
            return
        logger.debug(
            "Frame %d — pessoas: %d, EPIs: %d, violações: %d (conf=%.2f)",
            self._frame_count,
            len(detections.persons),
            len(detections.ppe_items),
            len(detections.violations),
            self._config.model.confidence,
        )

    def _parse_results(self, result: Results) -> FrameDetections:
        detections = FrameDetections()
        if result.boxes is None:
            return detections

        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls[0])
            bbox = BoundingBox(
                x1=box.xyxy[0][0], y1=box.xyxy[0][1],
                x2=box.xyxy[0][2], y2=box.xyxy[0][3],
                label=names[cls_id],
                confidence=float(box.conf[0]),
                track_id=int(box.id[0]) if box.id is not None else None,
            )

            if cls_id in self._class_groups["person"]:
                detections.persons.append(bbox)
            elif cls_id in self._class_groups["ppe"]:
                detections.ppe_items.append(bbox)
            elif cls_id in self._class_groups["violation"]:
                detections.violations.append(bbox)

        return detections


PPEDetector = YOLODetector
