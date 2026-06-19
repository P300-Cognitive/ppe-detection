from __future__ import annotations

import logging
import time
from typing import Iterator

import cv2
import numpy as np

from ppe_detection.config import CameraConfig

logger = logging.getLogger(__name__)


class CameraError(Exception):
    """Erro ao conectar ou ler frames da câmera."""


class CameraCapture:
    """Captura vídeo de câmera USB ou stream RTSP (US-001)."""

    def __init__(self, config: CameraConfig) -> None:
        self._config = config
        self._cap: cv2.VideoCapture | None = None
        self._source = self._parse_source(config.source)

    @staticmethod
    def _parse_source(source: str) -> int | str:
        if source.isdigit():
            return int(source)
        return source

    @property
    def is_rtsp(self) -> bool:
        return isinstance(self._source, str) and self._source.lower().startswith("rtsp")

    def connect(self) -> None:
        self.release()

        if self.is_rtsp:
            self._cap = cv2.VideoCapture(self._source, cv2.CAP_FFMPEG)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            self._cap = cv2.VideoCapture(self._source)

        if self._config.width > 0:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
        if self._config.height > 0:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)

        if not self._cap.isOpened():
            raise CameraError(
                f"Não foi possível conectar à câmera: {self._config.source}"
            )

        logger.info("Câmera conectada: %s", self._config.source)

    def read(self) -> np.ndarray | None:
        if self._cap is None or not self._cap.isOpened():
            return None

        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        return frame

    def frames(self) -> Iterator[np.ndarray]:
        """Gera frames continuamente, reconectando em caso de falha (US-002)."""
        while True:
            if self._cap is None or not self._cap.isOpened():
                try:
                    self.connect()
                except CameraError as exc:
                    logger.error("%s. Tentando novamente em %.0fs...", exc, self._config.reconnect_delay_sec)
                    time.sleep(self._config.reconnect_delay_sec)
                    continue

            frame = self.read()
            if frame is None:
                logger.warning("Perda de quadro ou câmera desconectada.")
                self.release()
                time.sleep(self._config.reconnect_delay_sec)
                continue

            yield frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> CameraCapture:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.release()
