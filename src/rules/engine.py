"""Motor de regras de segurança: confirma ausências de EPI e gera alertas/eventos."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from src.core.models import Alert, Event


class SafetyRulesEngine:
    """Avalia ausências de EPI por pessoa, emite alertas após limiar de confirmação
    e persiste eventos para auditoria.

    Também gerencia regras de EPIs obrigatórios por câmera.
    """

    def __init__(self, camera_id: str = "default"):
        self._camera_id = camera_id
        self._violation_counts: Dict[tuple, int] = defaultdict(int)
        self._pending_alerts: Dict[int, Alert] = {}
        self._recorded_events: List[Event] = []
        self._required_ppe: Dict[str, List[str]] = {}

    # ── Avaliação de conformidade ────────────────────────────────────────

    def evaluate(self, person_id: int, missing_ppe: str, threshold: int):
        """Incrementa contador de ausência; emite alerta ao atingir o limiar."""
        key = (person_id, missing_ppe)
        self._violation_counts[key] += 1
        if self._violation_counts[key] >= threshold:
            self._pending_alerts[person_id] = Alert(
                person_id=person_id,
                ppe_type=missing_ppe,
                camera_id=self._camera_id,
            )

    def get_pending_alert(self, person_id: int) -> Optional[Alert]:
        return self._pending_alerts.get(person_id)

    # ── Processamento de alertas ─────────────────────────────────────────

    def force_alert(self, person_id: int, ppe_type: str):
        """Força criação de alerta (usado em testes e integrações externas)."""
        self._pending_alerts[person_id] = Alert(
            person_id=person_id,
            ppe_type=ppe_type,
            camera_id=self._camera_id,
        )

    def process_alerts(self):
        """Converte alertas pendentes em eventos registrados e limpa a fila."""
        for alert in self._pending_alerts.values():
            self._recorded_events.append(
                Event(
                    person_id=alert.person_id,
                    camera_id=alert.camera_id or self._camera_id,
                    timestamp=datetime.now(),
                    ppe_type=alert.ppe_type,
                )
            )
        self._pending_alerts.clear()

    def get_recorded_events(self) -> List[Event]:
        return list(self._recorded_events)

    # ── Regras por câmera ────────────────────────────────────────────────

    def set_required_ppe(self, camera_id: str, ppe_list: List[str]):
        self._required_ppe[camera_id] = list(ppe_list)

    def get_required_ppe(self, camera_id: str) -> List[str]:
        return list(self._required_ppe.get(camera_id, []))
