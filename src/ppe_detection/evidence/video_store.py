"""Gravação de vídeo de ocorrências — spec: specs/contracts/evidence.yaml."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from ppe_detection.config import EvidenceConfig
from ppe_detection.evidence.video_buffer import VideoRingBuffer

logger = logging.getLogger(__name__)


@dataclass
class _PendingRecording:
    track_id: int
    reason: str
    frames: list[np.ndarray] = field(default_factory=list)
    post_remaining: int = 0


class VideoEvidenceStore:
    """Implementa VideoEvidencePort — US-015."""

    def __init__(self, config: EvidenceConfig) -> None:
        self._config = config
        max_frames = int(config.video_pre_seconds * config.video_fps)
        self._buffer = VideoRingBuffer(max_frames)
        self._pending: list[_PendingRecording] = []

    def push_frame(self, frame: np.ndarray) -> None:
        if not self._config.save_video:
            return
        self._buffer.push(frame)

    def on_alert(
        self,
        frame: np.ndarray,
        output_dir: Path,
        track_id: int,
        reason: str,
    ) -> Path | None:
        if not self._config.save_video:
            return None

        pre = self._buffer.snapshot()
        post_needed = int(self._config.video_post_seconds * self._config.video_fps)
        recording = _PendingRecording(
            track_id=track_id,
            reason=reason,
            frames=pre + [frame.copy()],
            post_remaining=post_needed,
        )

        if post_needed == 0:
            return self._write_video(recording, output_dir)

        self._pending.append(recording)
        return None

    def tick(self, frame: np.ndarray, output_dir: Path) -> list[Path]:
        if not self._config.save_video or not self._pending:
            return []

        finished: list[Path] = []
        still_pending: list[_PendingRecording] = []

        for rec in self._pending:
            rec.frames.append(frame.copy())
            rec.post_remaining -= 1
            if rec.post_remaining <= 0:
                path = self._write_video(rec, output_dir)
                finished.append(path)
            else:
                still_pending.append(rec)

        self._pending = still_pending
        return finished

    def _write_video(self, recording: _PendingRecording, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"alert_{recording.track_id}_{timestamp}.mp4"
        path = output_dir / filename

        if not recording.frames:
            logger.warning("Gravação vazia para track %s", recording.track_id)
            return path

        h, w = recording.frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, self._config.video_fps, (w, h))

        for f in recording.frames:
            writer.write(f)
        writer.release()

        logger.info("Vídeo de evidência salvo: %s", path)
        return path
