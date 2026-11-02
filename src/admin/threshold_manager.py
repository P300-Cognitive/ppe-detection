"""Gerenciamento de limiares de confiança por classe de EPI, com hot-reload."""
from __future__ import annotations

from typing import Dict

_DEFAULT = 0.5


class ThresholdManager:
    """Ajusta limiares de detecção por classe sem reiniciar o sistema."""

    def __init__(self):
        self._thresholds: Dict[str, float] = {}
        self._running = False

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def set(self, ppe_class: str, value: float):
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"Limiar deve estar entre 0.0 e 1.0, recebido: {value}"
            )
        self._thresholds[ppe_class] = value

    def get(self, ppe_class: str) -> float:
        return self._thresholds.get(ppe_class, _DEFAULT)

    def get_all(self) -> Dict[str, float]:
        return dict(self._thresholds)

    def remove(self, ppe_class: str):
        self._thresholds.pop(ppe_class, None)
