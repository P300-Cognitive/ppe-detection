"""Persistência de evidências de alerta."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from ppe_detection.config import AppConfig
from ppe_detection.contracts.ports import EvidencePort
from ppe_detection.domain.models import PersonCompliance
from ppe_detection.evidence.video_store import VideoEvidenceStore
from ppe_detection.storage.occurrence_store import OccurrenceRecord, OccurrenceStore

logger = logging.getLogger(__name__)


class EvidenceHandler:
    def __init__(
        self,
        config: AppConfig,
        evidence: EvidencePort,
        video_store: VideoEvidenceStore,
        occurrence_store: OccurrenceStore | None,
        camera_id: str = "default",
    ) -> None:
        self._config = config
        self._evidence = evidence
        self._video_store = video_store
        self._occurrence_store = occurrence_store
        self._camera_id = camera_id
        self._saved_alerts: set[int] = set()
        self._pending_video_occ: dict[int, int] = {}
        self._output_dir = Path(config.evidence.output_dir)

    def process_frame(self, frame: np.ndarray, compliance: list[PersonCompliance]) -> None:
        if not self._config.evidence.enabled or not self._config.evidence.save_on_alert:
            return

        for vpath in self._video_store.tick(frame, self._output_dir):
            self._attach_video_to_pending(vpath)

        for person in compliance:
            if not person.alert:
                self._saved_alerts.discard(person.track_id)
                continue
            if person.track_id in self._saved_alerts:
                continue
            self._save_alert(frame, person)

    def _attach_video_to_pending(self, vpath: Path) -> None:
        for occ_id in self._pending_video_occ.values():
            if self._occurrence_store:
                self._occurrence_store.update_video_path(occ_id, str(vpath))
            break

    def _save_alert(self, frame: np.ndarray, person: PersonCompliance) -> None:
        img_path = self._evidence.save(
            frame, self._output_dir, person.track_id, person.alert_reason,
        )
        vid_path = self._video_store.on_alert(
            frame, self._output_dir, person.track_id, person.alert_reason,
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
