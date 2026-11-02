"""Histórico de ocorrências de não conformidades para consulta e auditoria."""
from __future__ import annotations

from typing import Any, List, Optional


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
            results = [i for i in results if str(i.date) == date]
        if camera_id is not None:
            results = [i for i in results if i.camera_id == camera_id]
        if ppe_type is not None:
            results = [i for i in results if i.ppe_type == ppe_type]
        return results

    def all(self) -> List[Any]:
        return list(self._incidents)

    def count(self) -> int:
        return len(self._incidents)
