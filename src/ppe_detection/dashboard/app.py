"""API do dashboard — spec: specs/contracts/dashboard.yaml."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import cv2
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from ppe_detection.config import AppConfig, load_cameras_config, load_config
from ppe_detection.dashboard.reports import export_report, generate_summary
from ppe_detection.dashboard.service import DashboardService
from ppe_detection.domain.ppe import ppe_label
from ppe_detection.storage.occurrence_store import OccurrenceStore

STATIC_DIR = Path(__file__).parent / "static"


def _record_to_dict(record) -> dict:
    return {
        "id": record.id,
        "camera_id": record.camera_id,
        "track_id": record.track_id,
        "reason": record.reason,
        "missing_ppe": record.missing_ppe,
        "created_at": record.created_at.isoformat(),
        "image_path": record.image_path,
        "video_path": record.video_path,
    }


def create_app(
    config: AppConfig | None = None,
    service: DashboardService | None = None,
    store: OccurrenceStore | None = None,
) -> FastAPI:
    config = config or load_config()
    store = store or OccurrenceStore(config.storage.db_path)
    owns_service = service is None

    if service is None:
        cameras = load_cameras_config(config.dashboard.cameras_file)
        service = DashboardService(config, cameras, store)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if owns_service:
            service.start()
        yield
        if owns_service:
            service.stop()

    app = FastAPI(title="PPE Detection Dashboard", version="0.1.0", lifespan=lifespan)
    app.state.service = service
    app.state.store = store
    app.state.config = config

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/dashboard/")

    @app.get("/api/status")
    def status() -> dict:
        return {
            "required_ppe": config.rules.required_ppe,
            "required_ppe_labels": [ppe_label(k) for k in config.rules.required_ppe],
            "model": config.model.path,
            "confidence": config.model.confidence,
            "cameras_count": len(load_cameras_config(config.dashboard.cameras_file)),
            "evidence_enabled": config.evidence.enabled,
        }

    @app.get("/api/cameras")
    def list_cameras() -> list[dict]:
        return service.get_cameras()

    @app.get("/api/cameras/{camera_id}/snapshot")
    def camera_snapshot(camera_id: str) -> Response:
        frame = service.get_snapshot(camera_id)
        if frame is None:
            raise HTTPException(404, "Câmera sem frame disponível")
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            raise HTTPException(500, "Erro ao codificar imagem")
        return Response(content=buf.tobytes(), media_type="image/jpeg")

    @app.get("/api/alerts/recent")
    def recent_alerts(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
        records = store.search(limit=limit)
        return [_record_to_dict(r) for r in records]

    @app.get("/api/occurrences")
    def search_occurrences(
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        camera_id: str | None = None,
        ppe_type: str | None = None,
        limit: int = Query(100, ge=1, le=1000),
    ) -> list[dict]:
        records = store.search(from_date, to_date, camera_id, ppe_type, limit)
        return [_record_to_dict(r) for r in records]

    @app.get("/api/reports/summary")
    def report_summary(
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        camera_id: str | None = None,
    ) -> dict:
        return generate_summary(store, from_date, to_date, camera_id)

    @app.get("/api/reports/export")
    def report_export(
        fmt: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        camera_id: str | None = None,
    ) -> FileResponse:
        out_dir = Path(config.storage.reports_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"report_{ts}.{fmt}"
        export_report(store, path, fmt, from_date, to_date, camera_id)
        media = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if fmt == "xlsx" else "application/pdf"
        )
        return FileResponse(path, media_type=media, filename=path.name)

    if STATIC_DIR.exists():
        app.mount("/dashboard", StaticFiles(directory=STATIC_DIR, html=True), name="dashboard")

    return app
