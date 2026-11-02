"""Processamento contínuo de quadros com controle de FPS."""
from __future__ import annotations

import collections
import threading
import time
from typing import Callable, Optional

import numpy as np

from src.video.capture import VideoCapture


class FrameProcessor:
    """Captura e processa quadros em thread dedicada, mantendo FPS mínimo."""

    def __init__(self, source: int | str | None = None, min_fps: int = 15):
        self._source = source
        self._min_fps = min_fps
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._capture: Optional[VideoCapture] = None
        self._fps_samples: collections.deque = collections.deque(maxlen=30)
        self._on_frame: Optional[Callable[[np.ndarray], None]] = None

    def set_min_fps(self, fps: int):
        self._min_fps = fps

    def on_frame(self, callback: Callable[[np.ndarray], None]):
        """Registra callback chamado a cada quadro processado."""
        self._on_frame = callback

    def start(self):
        self._running = True
        if self._source is not None:
            self._capture = VideoCapture(self._source)
            self._capture.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._capture:
            self._capture.stop()
        if self._thread:
            self._thread.join(timeout=2.0)

    def is_running(self) -> bool:
        return self._running

    def get_current_fps(self) -> float:
        if len(self._fps_samples) < 2:
            return float(self._min_fps)
        intervals = [
            self._fps_samples[i] - self._fps_samples[i - 1]
            for i in range(1, len(self._fps_samples))
        ]
        mean_interval = sum(intervals) / len(intervals)
        return round(1.0 / mean_interval, 2) if mean_interval > 0 else 0.0

    def simulate_frame_drop(self, count: int = 3):
        """Stub para testes — simula perda de quadros sem parar o processamento."""
        pass

    def _loop(self):
        while self._running:
            t0 = time.perf_counter()
            self._fps_samples.append(t0)
            if self._capture:
                frame = self._capture.read()
                if frame is not None and self._on_frame:
                    self._on_frame(frame)
            elapsed = time.perf_counter() - t0
            sleep = max(0.0, (1.0 / self._min_fps) - elapsed)
            if sleep > 0:
                time.sleep(sleep)
