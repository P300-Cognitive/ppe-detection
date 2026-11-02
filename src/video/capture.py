"""Captura de vídeo a partir de câmera USB ou stream RTSP."""
from __future__ import annotations

from typing import Optional
import numpy as np
import cv2


class VideoCapture:
    """Abre e mantém a conexão com uma câmera USB (índice int) ou RTSP (URL str)."""

    def __init__(self, source: int | str):
        self._source = source
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False

    def start(self):
        self._cap = cv2.VideoCapture(self._source)
        if not self._cap.isOpened():
            self._running = False
            self._cap.release()
            self._cap = None
            raise ConnectionError(
                f"Não foi possível conectar à câmera: {self._source!r}"
            )
        self._running = True

    def stop(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._running = False

    def is_running(self) -> bool:
        return self._running and self._cap is not None and self._cap.isOpened()

    def read(self) -> Optional[np.ndarray]:
        if not self.is_running():
            raise RuntimeError("Captura não iniciada — chame start() primeiro.")
        ret, frame = self._cap.read()
        return frame if ret else None
