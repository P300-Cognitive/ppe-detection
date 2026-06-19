"""Orquestração multi-câmera para o dashboard — US-017."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field, replace

import numpy as np

from ppe_detection.association.matcher import create_associator
from ppe_detection.camera.capture import CameraCapture
from ppe_detection.config import AppConfig, CameraEntry
from ppe_detection.detection.detector import YOLODetector
from ppe_detection.evidence.handler import EvidenceHandler
from ppe_detection.evidence.video_store import VideoEvidenceStore
from ppe_detection.rules.safety import SafetyRulesEngine
from ppe_detection.storage.occurrence_store import OccurrenceStore
from ppe_detection.visualization.renderer import EvidenceStore, FrameRenderer

logger = logging.getLogger(__name__)


@dataclass
class CameraState:
    camera_id: str
    name: str
    source: str
    status: str = "stopped"
    last_frame: np.ndarray | None = None
    last_compliance: list = field(default_factory=list)
    fps: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)


class DashboardService:
    """Gerencia pipelines de múltiplas câmeras em background."""

    def __init__(
        self,
        config: AppConfig,
        cameras: list[CameraEntry],
        store: OccurrenceStore,
    ) -> None:
        self._config = config
        self._cameras = cameras
        self._store = store
        self._states: dict[str, CameraState] = {}
        self._threads: list[threading.Thread] = []
        self._stop = threading.Event()

        for cam in cameras:
            self._states[cam.id] = CameraState(
                camera_id=cam.id, name=cam.name, source=cam.source,
            )

    def start(self) -> None:
        self._stop.clear()
        for cam in self._cameras:
            t = threading.Thread(
                target=self._run_camera, args=(cam,),
                daemon=True, name=f"camera-{cam.id}",
            )
            t.start()
            self._threads.append(t)
        logger.info("Dashboard: %d câmera(s) iniciada(s)", len(self._cameras))

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=5)
        self._threads.clear()

    def get_cameras(self) -> list[dict]:
        result = []
        for state in self._states.values():
            with state.lock:
                alerts = sum(1 for c in state.last_compliance if getattr(c, "alert", False))
                result.append({
                    "id": state.camera_id,
                    "name": state.name,
                    "source": state.source,
                    "status": state.status,
                    "fps": round(state.fps, 1),
                    "active_alerts": alerts,
                })
        return result

    def get_snapshot(self, camera_id: str) -> np.ndarray | None:
        state = self._states.get(camera_id)
        if not state:
            return None
        with state.lock:
            return state.last_frame.copy() if state.last_frame is not None else None

    def _run_camera(self, cam: CameraEntry) -> None:
        state = self._states[cam.id]
        camera = CameraCapture(replace(self._config.camera, source=cam.source))
        detector = YOLODetector(self._config)
        rules = SafetyRulesEngine(self._config, create_associator(self._config))
        renderer = FrameRenderer(self._config)
        video_store = VideoEvidenceStore(self._config.evidence)
        evidence_handler = EvidenceHandler(
            config=self._config,
            evidence=EvidenceStore(),
            video_store=video_store,
            occurrence_store=self._store,
            camera_id=cam.id,
        )
        frame_times: deque[float] = deque(maxlen=30)
        state.status = "connecting"

        try:
            for frame in camera.frames():
                if self._stop.is_set():
                    break

                state.status = "running"
                start = time.perf_counter()

                detections = detector.detect(frame)
                compliance = rules.evaluate(detections)

                frame_times.append(time.perf_counter() - start)
                fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0

                rendered = renderer.render(frame, detections, compliance, fps)
                video_store.push_frame(rendered)
                evidence_handler.process_frame(rendered, compliance)

                with state.lock:
                    state.last_frame = rendered
                    state.last_compliance = compliance
                    state.fps = fps
        except Exception:
            logger.exception("Erro na câmera %s", cam.id)
            state.status = "error"
        finally:
            camera.release()
            if state.status != "error":
                state.status = "stopped"
