from __future__ import annotations

import logging
import time
from collections import deque

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
from ppe_detection.evidence.handler import EvidenceHandler
from ppe_detection.evidence.video_store import VideoEvidenceStore
from ppe_detection.rules.safety import SafetyRulesEngine
from ppe_detection.storage.occurrence_store import OccurrenceStore
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
        self._camera = camera or CameraCapture(config.camera)
        self._detector = detector or YOLODetector(config)
        associator = create_associator(config)
        self._rules = rules or SafetyRulesEngine(config, associator)
        self._renderer = renderer or FrameRenderer(config)
        self._video_store = video_store or VideoEvidenceStore(config.evidence)

        if occurrence_store is None and config.storage.db_path:
            occurrence_store = OccurrenceStore(config.storage.db_path)

        self._evidence_handler = EvidenceHandler(
            config=config,
            evidence=evidence or EvidenceStore(),
            video_store=self._video_store,
            occurrence_store=occurrence_store,
            camera_id=camera_id,
        )
        self._frame_times: deque[float] = deque(maxlen=30)

    def run(self, show: bool = True) -> None:
        logger.info("Iniciando pipeline de detecção de EPI...")
        logger.info("EPIs monitorados: %s", ", ".join(self._config.rules.required_ppe))
        logger.info("Pressione 'q' para sair.")

        win = self._config.display.window_name
        if show:
            cv2.namedWindow(win, cv2.WINDOW_NORMAL)

        try:
            for frame in self._camera.frames():
                start = time.perf_counter()

                detections = self._detector.detect(frame)
                compliance = self._rules.evaluate(detections)

                self._frame_times.append(time.perf_counter() - start)
                fps = 1.0 / (sum(self._frame_times) / len(self._frame_times))

                rendered = self._renderer.render(frame, detections, compliance, fps)
                self._video_store.push_frame(rendered)
                self._evidence_handler.process_frame(rendered, compliance)

                if show:
                    cv2.imshow(win, rendered)
                    if (cv2.waitKey(1) & 0xFF) == ord("q"):
                        break
        finally:
            self._camera.release()
            cv2.destroyAllWindows()
            logger.info("Pipeline encerrado.")
