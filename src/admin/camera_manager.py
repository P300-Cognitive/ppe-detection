"""Gerenciamento de câmeras: cadastro, teste de conectividade e enable/disable."""
from __future__ import annotations

import uuid
from typing import Dict, List, Optional

import cv2

from src.core.models import Camera, ConnectivityStatus


class CameraManager:
    """Gerencia o ciclo de vida de câmeras cadastradas no sistema."""

    def __init__(self):
        self._cameras: Dict[str, Camera] = {}

    def register(self, rtsp_url: str) -> Camera:
        cam_id = f"CAM-{uuid.uuid4().hex[:8].upper()}"
        camera = Camera(id=cam_id, rtsp_url=rtsp_url, enabled=True)
        self._cameras[cam_id] = camera
        return camera

    def get(self, camera_id: str) -> Optional[Camera]:
        return self._cameras.get(camera_id)

    def list_all(self) -> List[Camera]:
        return list(self._cameras.values())

    def list_enabled(self) -> List[Camera]:
        return [c for c in self._cameras.values() if c.enabled]

    def test_connectivity(self, rtsp_url: str) -> ConnectivityStatus:
        try:
            cap = cv2.VideoCapture(rtsp_url)
            reachable = cap.isOpened()
            cap.release()
            return ConnectivityStatus(is_reachable=reachable)
        except Exception as exc:
            return ConnectivityStatus(is_reachable=False, error=str(exc))

    def enable(self, camera_id: str):
        if camera_id in self._cameras:
            self._cameras[camera_id].enabled = True

    def disable(self, camera_id: str):
        if camera_id in self._cameras:
            self._cameras[camera_id].enabled = False
