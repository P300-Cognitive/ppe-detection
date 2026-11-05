"""Painel de monitoramento em tempo real de câmeras e alertas EPI."""
from __future__ import annotations

from typing import Any, List

from src.core.models import Alert, DashboardView


class DashboardMonitor:
    """Centraliza streams de múltiplas câmeras e exibe alertas em tempo real."""

    def __init__(self):
        self._cameras: List[str] = []
        self._alerts: List[Alert] = []
        self._running = False

    def register_camera(self, camera_id: str):
        if camera_id not in self._cameras:
            self._cameras.append(camera_id)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def get_current_view(self) -> DashboardView:
        return DashboardView(
            active_streams=list(self._cameras),
            active_alerts=list(self._alerts),
        )

    def push_alert(self, alert: Any):
        if not isinstance(alert, Alert):
            alert = Alert(
                person_id=getattr(alert, "person_id", 0),
                ppe_type=getattr(alert, "reason", "unknown"),
                camera_id=getattr(alert, "camera_id", None),
            )
        self._alerts.append(alert)

    def get_active_alerts(self) -> List[Alert]:
        return list(self._alerts)

    def set_active_alerts(self, alerts: List[Any]):
        """Substitui os alertas visíveis pelos que ainda valem neste momento."""
        active: List[Alert] = []
        seen = set()
        for alert in alerts:
            if not isinstance(alert, Alert):
                alert = Alert(
                    person_id=getattr(alert, "person_id", 0),
                    ppe_type=getattr(alert, "reason", getattr(alert, "ppe_type", "unknown")),
                    camera_id=getattr(alert, "camera_id", None),
                )
            raw = str(alert.ppe_type or "").lower()
            if raw.startswith("sem "):
                raw = raw[4:]
            key = (alert.person_id, raw)
            if key in seen:
                continue
            seen.add(key)
            active.append(alert)
        self._alerts = active

    def clear_alerts(self):
        self._alerts.clear()

    def retain_required(self, required: set[str]):
        """Mantém só alertas dos EPIs que continuam obrigatórios."""
        kept = []
        for alert in self._alerts:
            raw = str(getattr(alert, "ppe_type", "") or "").lower()
            if raw.startswith("sem "):
                raw = raw[4:]
            if raw in required:
                kept.append(alert)
        self._alerts = kept
