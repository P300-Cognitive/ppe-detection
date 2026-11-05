"""Rastreamento multi-pessoa entre quadros usando ByteTrack."""
from __future__ import annotations

from typing import List

import numpy as np
import supervision as sv
from trackers import ByteTrackTracker

from src.core.models import TrackedPerson
from src.detection.person import PersonDetector


class PersonTracker:
    """Mantém IDs persistentes de pessoas entre quadros consecutivos.

    Combina PersonDetector (YOLOv8) com ByteTrack para ID estável.
    """

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.5):
        self._detector = PersonDetector(model_path=model_path, confidence=confidence)
        # sv.ByteTrack foi removido no supervision 0.31; o pacote trackers
        # expõe o mesmo algoritmo via ByteTrackTracker.update().
        self._tracker = ByteTrackTracker(
            track_activation_threshold=0.25,
            minimum_consecutive_frames=1,
        )

    def reset(self):
        """Zera os IDs ao trocar a fonte de vídeo."""
        self._tracker = ByteTrackTracker(
            track_activation_threshold=0.25,
            minimum_consecutive_frames=1,
        )

    def update(self, frame: np.ndarray) -> List[TrackedPerson]:
        raw = self._detector.detect(frame)
        if not raw:
            self._tracker.update(sv.Detections.empty())
            return []

        xyxy = np.array([list(d.bbox) for d in raw], dtype=np.float32)
        confs = np.array([d.confidence for d in raw], dtype=np.float32)
        class_ids = np.zeros(len(raw), dtype=int)

        sv_dets = sv.Detections(xyxy=xyxy, confidence=confs, class_id=class_ids)
        tracked = self._tracker.update(sv_dets)

        results: List[TrackedPerson] = []
        if tracked.tracker_id is None:
            return results
        for i in range(len(tracked)):
            tid = int(tracked.tracker_id[i])
            if tid < 0:
                continue
            x1, y1, x2, y2 = tracked.xyxy[i].astype(int).tolist()
            results.append(TrackedPerson(track_id=tid, bbox=(x1, y1, x2, y2)))
        return results
