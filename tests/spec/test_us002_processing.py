"""US-002 — specs/features/epic-01-video.md"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ppe_detection.camera.capture import CameraCapture, CameraError
from ppe_detection.config import CameraConfig


@pytest.mark.spec("US-002")
class TestUS002Processing:
    def test_ac_002_1_frames_yields_from_connected_camera(self):
        cap = CameraCapture(CameraConfig(source="0", reconnect_delay_sec=0))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch.object(cap, "connect"), patch.object(cap, "read", side_effect=[frame, StopIteration]):
            cap._cap = MagicMock()  # noqa: SLF001
            cap._cap.isOpened.return_value = True  # noqa: SLF001
            gen = cap.frames()
            result = next(gen)
            assert result is frame

    def test_ac_002_2_recovers_from_none_frame(self):
        cap = CameraCapture(CameraConfig(source="0", reconnect_delay_sec=0))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with patch.object(cap, "connect"), patch.object(cap, "release"):
            cap._cap = MagicMock()  # noqa: SLF001
            cap._cap.isOpened.return_value = True  # noqa: SLF001
            with patch.object(cap, "read", side_effect=[None, frame, StopIteration]):
                gen = cap.frames()
                assert next(gen) is frame
