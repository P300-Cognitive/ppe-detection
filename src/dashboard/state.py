"""Estado compartilhado entre o pipeline de vídeo e o dashboard Flask."""
from __future__ import annotations

import threading
from typing import List, Optional

import numpy as np

from src.admin.camera_manager import CameraManager
from src.admin.model_manager import ModelManager
from src.admin.threshold_manager import ThresholdManager
from src.dashboard.monitor import DashboardMonitor
from src.reports.history import IncidentHistory
from src.rules.engine import SafetyRulesEngine


class AppState:
    """Singleton de estado da aplicação – thread-safe."""

    def __init__(self):
        self.cam_manager = CameraManager()
        self.model_manager = ModelManager()
        self.threshold_manager = ThresholdManager()
        self.monitor = DashboardMonitor()
        self.history = IncidentHistory()
        self.engine: Optional[SafetyRulesEngine] = None
        self.required_ppe: List[str] = []
        self.confirm_frames: int = 5
        self.pre_seconds: int = 10
        self.post_seconds: int = 5

        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()

    def setup(
        self,
        camera_id: str,
        required_ppe: List[str],
        confirm_frames: int,
        pre_seconds: int,
        post_seconds: int,
    ):
        self.required_ppe = required_ppe
        self.confirm_frames = confirm_frames
        self.pre_seconds = pre_seconds
        self.post_seconds = post_seconds
        self.engine = SafetyRulesEngine(camera_id=camera_id)
        self.engine.set_required_ppe(camera_id, required_ppe)
        self.threshold_manager.start()
        self.monitor.start()

    def update_frame(self, frame: np.ndarray):
        with self._lock:
            self._frame = frame.copy()

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None
