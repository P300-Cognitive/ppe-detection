"""Detecção de EPIs em frames usando YOLOv8 com modelo customizado."""
from __future__ import annotations

from typing import Dict, List, Optional

import cv2
import numpy as np
from ultralytics import YOLO

from src.core.models import Detection

# Mapeamento padrão de nome de classe → índice no modelo PPE.
# Substituir conforme as classes do modelo treinado.
DEFAULT_CLASS_LABELS: Dict[str, int] = {
    "helmet":  0,
    "vest":    1,
    "glasses": 2,
    "mask":    3,
    "gloves":  4,
    "boots":   5,
}

_RENDER_COLOR = (0, 255, 0)   # BGR verde para EPIs detectados


class PPEDetector:
    """Detecta EPIs num frame BGR.

    model_path: caminho para o modelo .pt treinado em EPIs.
                Se None, detect() retorna lista vazia até o modelo ser provido.
    classes:    lista de nomes de classe a detectar (ex: ['helmet', 'vest']).
    """

    def __init__(
        self,
        classes: List[str],
        model_path: Optional[str] = None,
        confidence: float = 0.5,
        class_labels: Optional[Dict[str, int]] = None,
    ):
        self._classes = classes
        self._confidence = confidence
        self._class_labels = class_labels or DEFAULT_CLASS_LABELS
        self._idx_to_name = {v: k for k, v in self._class_labels.items()}
        self._model: Optional[YOLO] = YOLO(model_path) if model_path else None

    def detect(self, frame: np.ndarray) -> List[Detection]:
        if self._model is None:
            return []
        indices = [
            self._class_labels[c]
            for c in self._classes
            if c in self._class_labels
        ]
        results = self._model(frame, classes=indices, conf=self._confidence, verbose=False)
        detections: List[Detection] = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                cls_idx = int(box.cls[0])
                detections.append(
                    Detection(
                        class_name=self._idx_to_name.get(cls_idx, str(cls_idx)),
                        confidence=float(box.conf[0]),
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return detections

    def render(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), _RENDER_COLOR, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(
                annotated, label, (x1, max(y1 - 6, 0)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, _RENDER_COLOR, 1,
            )
        return annotated
