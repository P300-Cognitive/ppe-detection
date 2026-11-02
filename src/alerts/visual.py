"""Renderização visual de alertas de não conformidade sobre o frame de vídeo."""
from __future__ import annotations

from typing import Any, List, Tuple

import cv2
import numpy as np

_COLOR_VIOLATION: Tuple[int, int, int] = (0, 0, 255)   # BGR vermelho
_COLOR_OK:        Tuple[int, int, int] = (0, 255, 0)   # BGR verde


class VisualAlertRenderer:
    """Anota frames com caixas vermelhas e rótulos para cada violação de EPI.

    Mantém estado da última renderização para que get_bbox_color e get_labels
    possam ser consultados nos testes sem depender de leitura de pixels.
    """

    def __init__(self):
        self._last_violations: List[Any] = []
        self._last_labels: List[str] = []

    def render(self, frame: np.ndarray, violations: List[Any]) -> np.ndarray:
        annotated = frame.copy()
        self._last_violations = list(violations)
        self._last_labels = []

        for v in violations:
            reason = getattr(v, "reason", "violação")
            self._last_labels.append(reason)

            bbox = getattr(v, "bbox", None)
            if bbox:
                x1, y1, x2, y2 = bbox
                cv2.rectangle(annotated, (x1, y1), (x2, y2), _COLOR_VIOLATION, 2)
                cv2.putText(
                    annotated, reason, (x1, max(y1 - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, _COLOR_VIOLATION, 2,
                )

        return annotated

    def get_bbox_color(
        self, rendered_frame: np.ndarray, person_id: int
    ) -> Tuple[int, int, int]:
        """Retorna a cor BGR da caixa delimitadora da pessoa na última renderização."""
        for v in self._last_violations:
            if getattr(v, "person_id", None) == person_id:
                return _COLOR_VIOLATION
        return _COLOR_OK

    def get_labels(self, rendered_frame: np.ndarray) -> List[str]:
        """Retorna os rótulos de alerta da última renderização."""
        return list(self._last_labels)
