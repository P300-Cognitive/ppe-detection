"""US-017 — specs/features/epic-07-dashboard.md"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from ppe_detection.config import AppConfig
from ppe_detection.dashboard.app import create_app


class _MockService:
    def start(self) -> None: ...
    def stop(self) -> None: ...

    def get_cameras(self) -> list[dict]:
        return [
            {"id": "cam1", "name": "Test", "source": "0", "status": "running", "fps": 15.0, "active_alerts": 0},
            {"id": "cam2", "name": "Test 2", "source": "1", "status": "running", "fps": 12.0, "active_alerts": 1},
        ]

    def get_snapshot(self, camera_id: str) -> np.ndarray | None:
        if camera_id == "cam1":
            return np.zeros((100, 100, 3), dtype=np.uint8)
        return None


@pytest.mark.spec("US-017")
class TestUS017Dashboard:
    @pytest.fixture
    def client(self, tmp_path):
        config = AppConfig()
        config.storage.db_path = str(tmp_path / "test.db")
        app = create_app(config=config, service=_MockService())
        return TestClient(app)

    def test_ac_017_1_lists_multiple_cameras(self, client):
        res = client.get("/api/cameras")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2

    def test_ac_017_2_snapshot_returns_jpeg(self, client):
        res = client.get("/api/cameras/cam1/snapshot")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/jpeg"
