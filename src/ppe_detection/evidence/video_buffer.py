"""Buffer circular de frames — spec: specs/contracts/evidence.yaml."""

from __future__ import annotations

from collections import deque

import numpy as np


class VideoRingBuffer:
    """Mantém os últimos N frames para gravação pré-alerta."""

    def __init__(self, max_frames: int) -> None:
        self._max_frames = max(1, max_frames)
        self._frames: deque[np.ndarray] = deque(maxlen=self._max_frames)

    def push(self, frame: np.ndarray) -> None:
        self._frames.append(frame.copy())

    def snapshot(self) -> list[np.ndarray]:
        return [f.copy() for f in self._frames]

    def __len__(self) -> int:
        return len(self._frames)
