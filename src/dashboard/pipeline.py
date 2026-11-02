"""Pipeline completo: captura → detecção → rastreamento → regras → alertas."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

import cv2

from src.alerts.evidence import EvidenceRecorder
from src.alerts.visual import VisualAlertRenderer
from src.association.associator import PPEAssociator
from src.core.models import Violation
from src.detection.ppe import PPEDetector
from src.notifications.notifier import NotificationService
from src.tracking.tracker import PersonTracker
from src.video.capture import VideoCapture

if TYPE_CHECKING:
    from src.dashboard.state import AppState


class CameraPipeline:
    """Executa o loop de processamento de vídeo em thread separada.

    Publica o frame anotado em AppState para streaming MJPEG pelo dashboard.
    """

    def __init__(
        self,
        source: int | str,
        camera_id: str,
        ppe_model: Optional[str],
        confidence: float,
        min_fps: int,
        show_window: bool,
        state: "AppState",
    ):
        self._source = source
        self._camera_id = camera_id
        self._ppe_model = ppe_model
        self._confidence = confidence
        self._min_fps = min_fps
        self._show_window = show_window
        self._state = state
        self._running = False

    # ── Ciclo principal ───────────────────────────────────────────────────

    def run(self):
        self._running = True
        capture = VideoCapture(self._source)
        try:
            capture.start()
        except ConnectionError as exc:
            print(f"[pipeline] ERRO ao conectar câmera: {exc}")
            return

        tracker = PersonTracker(confidence=self._confidence)
        ppe_detector = PPEDetector(
            classes=self._state.required_ppe,
            model_path=self._ppe_model,
            confidence=self._confidence,
        )
        associator = PPEAssociator()
        renderer = VisualAlertRenderer()
        recorder = EvidenceRecorder(
            pre_alert_seconds=self._state.pre_seconds,
            post_alert_seconds=self._state.post_seconds,
        )
        notifier = NotificationService(channels=["telegram", "email"])

        frame_interval = 1.0 / self._min_fps
        print(f"[pipeline] Processando {self._camera_id} @ {self._min_fps} FPS mín.")

        while self._running and capture.is_running():
            t0 = time.perf_counter()

            frame = capture.read()
            if frame is None:
                time.sleep(0.01)
                continue

            # ── Detecção e rastreamento ──────────────────────────────────
            persons = tracker.update(frame)
            ppe_dets = ppe_detector.detect(frame)
            associations = associator.associate(persons, ppe_dets)

            # ── Avaliação de regras ──────────────────────────────────────
            violations = []
            violating_ids: set = set()
            person_bbox = {p.track_id: p.bbox for p in persons}

            for person in persons:
                owned = associations.get(person.track_id, [])
                for required in self._state.required_ppe:
                    if required not in owned:
                        self._state.engine.evaluate(
                            person_id=person.track_id,
                            missing_ppe=required,
                            threshold=self._state.confirm_frames,
                        )
                        if self._state.engine.get_pending_alert(person.track_id):
                            violating_ids.add(person.track_id)
                            violations.append(
                                Violation(
                                    person_id=person.track_id,
                                    reason=f"sem {required}",
                                    camera_id=self._camera_id,
                                    bbox=person.bbox,
                                )
                            )

            # ── Anotação visual ──────────────────────────────────────────
            annotated = frame.copy()

            # Pessoas detectadas: verde (conforme) ou vermelho (violação)
            for person in persons:
                x1, y1, x2, y2 = person.bbox
                color = (0, 0, 255) if person.track_id in violating_ids else (0, 220, 0)
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"P{person.track_id}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            # EPIs detectados: caixas ciano com nome da classe e confiança
            for det in ppe_dets:
                x1, y1, x2, y2 = det.bbox
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 200, 0), 2)
                lbl = f"{det.class_name} {det.confidence:.0%}"
                cv2.putText(annotated, lbl, (x1, max(y1 - 6, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 200, 0), 1)

            # Motivos de violação em vermelho sobre a caixa da pessoa
            shown_reasons: set = set()
            for v in violations:
                key = (v.person_id, v.reason)
                if v.bbox and key not in shown_reasons:
                    shown_reasons.add(key)
                    x1, y1 = v.bbox[0], v.bbox[1]
                    cv2.putText(annotated, v.reason.upper(), (x1, max(y1 - 28, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Overlay de status no canto superior esquerdo
            fps_actual = round(1.0 / max(time.perf_counter() - t0, 1e-6), 1)
            overlay_lines = [
                f"{self._camera_id}",
                f"Pessoas: {len(persons)}",
                f"Alertas: {len(set(v.person_id for v in violations))}",
            ]
            for i, line in enumerate(overlay_lines):
                y = 22 + i * 22
                cv2.putText(annotated, line, (8, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            # Mensagem central quando nenhuma pessoa é detectada
            if not persons:
                h, w = annotated.shape[:2]
                cv2.putText(annotated, "Aguardando deteccao...",
                            (w // 2 - 160, h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 80), 2)

            # Disponibiliza frame para o MJPEG stream
            self._state.update_frame(annotated)

            # ── Evidências e notificações ────────────────────────────────
            if violations:
                self._state.engine.process_alerts()
                for v in violations:
                    img_path = recorder.save_image(frame, v)
                    self._state.monitor.push_alert(v)
                    self._state.history.add(v)
                    notifier.send(v, image_path=img_path)

            # ── Janela OpenCV opcional ────────────────────────────────────
            if self._show_window:
                cv2.imshow(f"PPE – {self._camera_id}", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            elapsed = time.perf_counter() - t0
            sleep = frame_interval - elapsed
            if sleep > 0:
                time.sleep(sleep)

        capture.stop()
        if self._show_window:
            cv2.destroyAllWindows()
        print(f"[pipeline] {self._camera_id} encerrado.")

    def stop(self):
        self._running = False
