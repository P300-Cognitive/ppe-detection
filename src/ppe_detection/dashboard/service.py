"""Orquestração multi-câmera para o dashboard — US-017."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from ppe_detection.association.matcher import create_associator
from ppe_detection.camera.capture import CameraCapture
from ppe_detection.config import AppConfig, CameraEntry
from ppe_detection.detection.detector import YOLODetector
from ppe_detection.evidence.video_store import VideoEvidenceStore
from ppe_detection.rules.safety import SafetyRulesEngine
from ppe_detection.storage.occurrence_store import OccurrenceRecord, OccurrenceStore
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
                target=self._run_camera,
                args=(cam,),
                daemon=True,
                name=f"camera-{cam.id}",
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
            if state.last_frame is None:
                return None
            return state.last_frame.copy()

    def _run_camera(self, cam: CameraEntry) -> None:
        state = self._states[cam.id]
        cam_config = self._config.camera
        cam_config.source = cam.source

        camera = CameraCapture(cam_config)
        detector = YOLODetector(self._config)
        associator = create_associator(self._config)
        rules = SafetyRulesEngine(self._config, associator)
        renderer = FrameRenderer(self._config)
        evidence = EvidenceStore()
        video_store = VideoEvidenceStore(self._config.evidence)
        output_dir = Path(self._config.evidence.output_dir)
        frame_times: deque[float] = deque(maxlen=30)
        saved_alerts: set[int] = set()
        pending_video_occ: dict[int, int] = {}

        state.status = "connecting"

        try:
            for frame in camera.frames():
                if self._stop.is_set():
                    break

                state.status = "running"
                start = time.perf_counter()

                detections = detector.detect(frame)
                compliance = rules.evaluate(detections)

                elapsed = time.perf_counter() - start
                frame_times.append(elapsed)
                fps = 1.0 / (sum(frame_times) / len(frame_times)) if frame_times else 0

                rendered = renderer.render(frame, detections, compliance, fps)
                video_store.push_frame(rendered)

                if self._config.evidence.enabled:
                    for vpath in video_store.tick(rendered, output_dir):
                        for occ_id in pending_video_occ.values():
                            self._store.update_video_path(occ_id, str(vpath))
                            break

                    for person in compliance:
                        if not person.alert:
                            saved_alerts.discard(person.track_id)
                            continue
                        if person.track_id in saved_alerts:
                            continue

                        img_path = evidence.save(
                            rendered, output_dir, person.track_id, person.alert_reason
                        )
                        vid_path = video_store.on_alert(
                            rendered, output_dir, person.track_id, person.alert_reason
                        )
                        occ_id = self._store.record(OccurrenceRecord(
                            id=None,
                            camera_id=cam.id,
                            track_id=person.track_id,
                            reason=person.alert_reason,
                            missing_ppe=list(person.missing_ppe),
                            created_at=datetime.now(),
                            image_path=str(img_path),
                            video_path=str(vid_path) if vid_path else None,
                        ))
                        if vid_path is None:
                            pending_video_occ[person.track_id] = occ_id
                        saved_alerts.add(person.track_id)

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
