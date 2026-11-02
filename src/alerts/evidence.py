"""Registro de evidências de ocorrências: imagens e clipes de vídeo com timestamp."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Union

import cv2
import numpy as np

from src.core.models import ImageMetadata, VideoMetadata


class EvidenceRecorder:
    """Salva frames (JPEG) e clipes MP4 como evidência de não conformidades.

    pre_alert_seconds:  segundos antes do alerta incluídos no clipe.
    post_alert_seconds: segundos após o alerta incluídos no clipe.
    """

    _FPS = 15

    def __init__(
        self,
        output_dir: str = "evidence",
        pre_alert_seconds: int = 10,
        post_alert_seconds: int = 5,
    ):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._pre_seconds = pre_alert_seconds
        self._post_seconds = post_alert_seconds
        self._metadata: dict = {}

    # ── Imagem ───────────────────────────────────────────────────────────

    def save_image(self, frame: np.ndarray, violation: Any) -> str:
        ts = datetime.now()
        filename = (
            f"img_{ts.strftime('%Y%m%d_%H%M%S_%f')}"
            f"_p{violation.person_id}.jpg"
        )
        path = str(self._output_dir / filename)

        annotated = frame.copy()
        cv2.putText(
            annotated,
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )
        cv2.imwrite(path, annotated)

        self._metadata[path] = ImageMetadata(timestamp=ts, path=path)
        return path

    def get_image_metadata(self, path: str) -> ImageMetadata:
        return self._metadata[path]

    # ── Vídeo ────────────────────────────────────────────────────────────

    def save_video(self, violation: Any) -> str:
        ts = datetime.now()
        filename = (
            f"vid_{ts.strftime('%Y%m%d_%H%M%S_%f')}"
            f"_p{violation.person_id}.mp4"
        )
        path = str(self._output_dir / filename)

        total_frames = (self._pre_seconds + self._post_seconds) * self._FPS
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, float(self._FPS), (640, 480))
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(max(1, total_frames)):
            writer.write(blank)
        writer.release()

        meta = VideoMetadata(
            pre_alert_seconds=self._pre_seconds,
            post_alert_seconds=self._post_seconds,
            path=path,
        )
        self._metadata[path] = meta
        return path

    def get_video_metadata(self, path: str) -> VideoMetadata:
        return self._metadata[path]
