"""Detecção de pessoas em frames usando YOLOv8."""
from __future__ import annotations

from typing import List

import numpy as np
from ultralytics import YOLO

from src.core.models import Detection


class PersonDetector:
    """Detecta pessoas num frame BGR usando YOLOv8.

    Retorna lista de Detection com class_name='person', confidence e bbox.
    """

    _YOLO_PERSON_CLASS = 0  # índice 'person' no COCO

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.5):
        self._model = YOLO(model_path)
        self._confidence = confidence

    def detect(self, frame: np.ndarray) -> List[Detection]:
        results = self._model(
            frame,
            classes=[self._YOLO_PERSON_CLASS],
            conf=self._confidence,
            verbose=False,
        )
        detections: List[Detection] = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                detections.append(
                    Detection(
                        class_name="person",
                        confidence=float(box.conf[0]),
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return detections
