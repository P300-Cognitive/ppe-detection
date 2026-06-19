"""US-001 — specs/features/epic-01-video.md"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ppe_detection.camera.capture import CameraCapture, CameraError
from ppe_detection.config import CameraConfig
from ppe_detection.contracts.ports import CameraPort


@pytest.mark.spec("US-001")
class TestUS001Camera:
    """AC-001-1, AC-001-2, AC-001-3"""

    def test_ac_001_1_usb_source_parsed_as_int(self):
        cap = CameraCapture(CameraConfig(source="0"))
        assert cap._source == 0  # noqa: SLF001

    def test_ac_001_2_rtsp_source_detected(self):
        cap = CameraCapture(CameraConfig(source="rtsp://192.168.1.1/stream"))
        assert cap.is_rtsp is True

    def test_ac_001_3_connection_failure_raises_camera_error(self):
        cap = CameraCapture(CameraConfig(source="99"))
        with patch("cv2.VideoCapture") as mock_vc:
            mock_vc.return_value.isOpened.return_value = False
            with pytest.raises(CameraError, match="99"):
                cap.connect()

    def test_implements_camera_port(self):
        cap = CameraCapture(CameraConfig(source="0"))
        assert isinstance(cap, CameraPort)
