"""US-003 — specs/features/epic-02-people.md"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ppe_detection.config import AppConfig
from ppe_detection.detection.detector import YOLODetector


@pytest.mark.spec("US-003")
class TestUS003PersonDetection:
    def test_ac_003_1_person_box_goes_to_persons_list(self, app_config):
        mock_box = MagicMock()
        mock_box.cls = [11]
        mock_box.conf = [0.92]
        mock_box.xyxy = [np.array([10.0, 20.0, 100.0, 200.0])]
        mock_box.id = None

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {11: "Person"}

        with patch("ultralytics.YOLO") as mock_yolo:
            instance = mock_yolo.return_value
            instance.names = {11: "Person"}
            instance.predict.return_value = [mock_result]

            detector = YOLODetector(app_config)
            detector._class_groups = {"person": {11}, "ppe": set(), "violation": set()}  # noqa: SLF001

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            app_config.tracking.enabled = False
            detections = detector.detect(frame)

        assert len(detections.persons) == 1
        assert detections.persons[0].label == "Person"
