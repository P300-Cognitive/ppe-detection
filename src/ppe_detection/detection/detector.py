from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ppe_detection.config import AppConfig
from ppe_detection.detection.model_loader import resolve_model_path
from ppe_detection.domain.models import BoundingBox, FrameDetections

if TYPE_CHECKING:
    from ultralytics.engine.results import Results


class YOLODetector:
    """Implementa DetectorPort — specs/contracts/detector.yaml."""

    def __init__(self, config: AppConfig) -> None:
        from ultralytics import YOLO

        self._config = config
        model_path = resolve_model_path(config.model.path)
        self._model = YOLO(model_path)
        self._class_groups = self._build_class_groups()

    def _build_class_groups(self) -> dict[str, set[int]]:
        names = self._model.names
        label_to_id = {v: k for k, v in names.items()}

        groups: dict[str, set[int]] = {
            "person": set(),
            "ppe": set(),
            "violation": set(),
        }

        for label in self._config.classes.person:
            if label in label_to_id:
                groups["person"].add(label_to_id[label])

        ppe_labels = (
            self._config.classes.helmet
            + self._config.classes.vest
            + self._config.classes.gloves
            + self._config.classes.goggles
            + self._config.classes.mask
            + self._config.classes.boots
        )
        for label in ppe_labels:
            if label in label_to_id:
                groups["ppe"].add(label_to_id[label])

        for labels in self._config.classes.violation.values():
            for label in labels:
                if label in label_to_id:
                    groups["violation"].add(label_to_id[label])

        return groups

    def detect(self, frame: np.ndarray) -> FrameDetections:
        kwargs: dict = {
            "conf": self._config.model.confidence,
            "verbose": False,
        }
        if self._config.model.device:
            kwargs["device"] = self._config.model.device

        if self._config.tracking.enabled:
            results = self._model.track(
                frame,
                persist=True,
                tracker=self._config.tracking.tracker,
                **kwargs,
            )
        else:
            results = self._model.predict(frame, **kwargs)

        return self._parse_results(results[0])

    def _parse_results(self, result: Results) -> FrameDetections:
        detections = FrameDetections()
        boxes = result.boxes
        if boxes is None:
            return detections

        names = result.names
        for box in boxes:
            cls_id = int(box.cls[0])
            label = names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            track_id = int(box.id[0]) if box.id is not None else None

            bbox = BoundingBox(
                x1=x1, y1=y1, x2=x2, y2=y2,
                label=label,
                confidence=conf,
                track_id=track_id,
            )

            if cls_id in self._class_groups["person"]:
                detections.persons.append(bbox)
            elif cls_id in self._class_groups["ppe"]:
                detections.ppe_items.append(bbox)
            elif cls_id in self._class_groups["violation"]:
                detections.violations.append(bbox)

        return detections


# Alias para compatibilidade
PPEDetector = YOLODetector
