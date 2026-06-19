from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2

from ppe_detection.association.matcher import create_associator
from ppe_detection.camera.capture import CameraCapture
from ppe_detection.config import AppConfig
from ppe_detection.contracts.ports import (
    CameraPort,
    DetectorPort,
    EvidencePort,
    RendererPort,
    RulesEnginePort,
)
from ppe_detection.detection.detector import YOLODetector
from ppe_detection.evidence.video_store import VideoEvidenceStore
from ppe_detection.rules.safety import SafetyRulesEngine
from ppe_detection.storage.occurrence_store import OccurrenceRecord, OccurrenceStore
from ppe_detection.visualization.renderer import EvidenceStore, FrameRenderer

logger = logging.getLogger(__name__)


class PPEPipeline:
    """Orquestra ports do pipeline — spec: specs/architecture.md."""

    def __init__(
        self,
        config: AppConfig,
        camera: CameraPort | None = None,
        detector: DetectorPort | None = None,
        rules: RulesEnginePort | None = None,
        renderer: RendererPort | None = None,
        evidence: EvidencePort | None = None,
        video_store: VideoEvidenceStore | None = None,
        occurrence_store: OccurrenceStore | None = None,
        camera_id: str = "default",
    ) -> None:
        self._config = config
        self._camera_id = camera_id
        self._camera = camera or CameraCapture(config.camera)
        self._detector = detector or YOLODetector(config)
        associator = create_associator(config)
        self._rules = rules or SafetyRulesEngine(config, associator)
        self._renderer = renderer or FrameRenderer(config)
        self._evidence = evidence or EvidenceStore()
        self._video_store = video_store or VideoEvidenceStore(config.evidence)
        self._occurrence_store = occurrence_store
        if occurrence_store is None and config.storage.db_path:
            self._occurrence_store = OccurrenceStore(config.storage.db_path)
        self._frame_times: deque[float] = deque(maxlen=30)
        self._saved_alerts: set[int] = set()
        self._pending_video_occ: dict[int, int] = {}

    def run(self, show: bool = True) -> None:
        logger.info("Iniciando pipeline de detecção de EPI...")
        logger.info("Pressione 'q' para sair.")

        win = self._config.display.window_name
        if show:
            # Cria a janela uma única vez antes do loop para evitar duplicatas no Linux/Qt
            cv2.namedWindow(win, cv2.WINDOW_NORMAL)

        try:
            for frame in self._camera.frames():
                start = time.perf_counter()

                detections = self._detector.detect(frame)
                compliance = self._rules.evaluate(detections)

                elapsed = time.perf_counter() - start
                self._frame_times.append(elapsed)
                fps = 1.0 / (sum(self._frame_times) / len(self._frame_times))

                if fps < self._config.camera.min_fps:
                    logger.debug(
                        "FPS abaixo do mínimo: %.1f < %d",
                        fps, self._config.camera.min_fps,
                    )

                rendered = self._renderer.render(frame, detections, compliance, fps)
                self._video_store.push_frame(rendered)
                self._handle_evidence(rendered, compliance)

                if show:
                    cv2.imshow(win, rendered)
                    if (cv2.waitKey(1) & 0xFF) == ord("q"):
                        break
        finally:
            self._camera.release()
            cv2.destroyAllWindows()
            logger.info("Pipeline encerrado.")

    def _handle_evidence(self, frame, compliance) -> None:
        if not self._config.evidence.enabled or not self._config.evidence.save_on_alert:
            return

        output_dir = Path(self._config.evidence.output_dir)

        for vpath in self._video_store.tick(frame, output_dir):
            for occ_id in self._pending_video_occ.values():
                if self._occurrence_store:
                    self._occurrence_store.update_video_path(occ_id, str(vpath))
                break

        for person in compliance:
            if not person.alert:
                self._saved_alerts.discard(person.track_id)
                continue
            if person.track_id in self._saved_alerts:
                continue

            img_path = self._evidence.save(
                frame, output_dir, person.track_id, person.alert_reason
            )
            vid_path = self._video_store.on_alert(
                frame, output_dir, person.track_id, person.alert_reason
            )

            if self._occurrence_store:
                occ_id = self._occurrence_store.record(OccurrenceRecord(
                    id=None,
                    camera_id=self._camera_id,
                    track_id=person.track_id,
                    reason=person.alert_reason,
                    missing_ppe=list(person.missing_ppe),
                    created_at=datetime.now(),
                    image_path=str(img_path),
                    video_path=str(vid_path) if vid_path else None,
                ))
                if vid_path is None:
                    self._pending_video_occ[person.track_id] = occ_id

            logger.warning("Evidência salva: %s", img_path)
            self._saved_alerts.add(person.track_id)
