"""Histórico de ocorrências de não conformidades para consulta e auditoria."""
from __future__ import annotations

from typing import Any, List, Optional


def _incident_date(item) -> str:
    raw = getattr(item, "date", None)
    if raw is not None:
        return str(raw)[:10]
    ts = getattr(item, "timestamp", None)
    if hasattr(ts, "strftime"):
        return ts.strftime("%Y-%m-%d")
    return "" if ts is None else str(ts)[:10]


def _matches_ppe(item, ppe_type: str) -> bool:
    if getattr(item, "ppe_type", None) == ppe_type:
        return True
    reason = str(getattr(item, "reason", "") or "")
    return reason == ppe_type or reason == f"sem {ppe_type}"


class IncidentHistory:
    """Armazena ocorrências e permite filtragem por data, câmera e tipo de EPI."""

    def __init__(self):
        self._incidents: List[Any] = []

    def add(self, incident: Any):
        self._incidents.append(incident)

    def filter(
        self,
        date: Optional[str] = None,
        camera_id: Optional[str] = None,
        ppe_type: Optional[str] = None,
    ) -> List[Any]:
        results = self._incidents
        if date is not None:
            results = [i for i in results if _incident_date(i) == date]
        if camera_id is not None:
            results = [i for i in results if i.camera_id == camera_id]
        if ppe_type is not None:
            results = [i for i in results if _matches_ppe(i, ppe_type)]
        return results

    def all(self) -> List[Any]:
        return list(self._incidents)

    def count(self) -> int:
        return len(self._incidents)
