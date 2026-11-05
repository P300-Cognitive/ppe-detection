"""Pipeline completo: captura → detecção → rastreamento → regras → alertas."""
from __future__ import annotations

import threading
import time
import traceback
from typing import TYPE_CHECKING, Optional

import cv2
import numpy as np

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
        self._open_violations: set[tuple] = set()
        self._switch_lock = threading.Lock()
        self._switch_gen = 0
        self._switch_to: Optional[tuple] = None

    # ── Ciclo principal ───────────────────────────────────────────────────

    def request_switch(self, source: int | str | None, camera_id: str, label: str) -> int:
        """Pede a troca da fonte. A thread de vídeo abre a câmera e devolve o token."""
        with self._switch_lock:
            self._switch_gen += 1
            token = self._switch_gen
            if source == self._source and self._state.camera_status in {"live", "idle"}:
                self._camera_id = camera_id
                self._state.camera_id = camera_id
                self._state.camera_label = label
                self._state.camera_token = token
                if self._state.engine is not None:
                    self._state.engine.set_camera_id(camera_id)
                return token
            self._state.camera_status = "switching"
            self._state.camera_error = None
            self._switch_to = (source, camera_id, label, token)
            return token

    def wait_for_switch(self, token: int, timeout: float = 12) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._state.camera_token == token and self._state.camera_status in {"live", "idle", "error"}:
                return self._state.camera_status
            time.sleep(0.05)
        return "timeout"

    def _take_switch(self) -> Optional[tuple]:
        with self._switch_lock:
            pending = self._switch_to
            self._switch_to = None
            return pending

    def _release_camera(self, camera_id: str, label: str, token: int):
        """Solta o dispositivo e deixa o painel sem imagem ao vivo."""
        self._source = None
        self._camera_id = camera_id
        self._state.camera_source = None
        self._state.camera_id = camera_id
        self._state.camera_label = label
        self._state.camera_error = None
        self._state.camera_status = "idle"
        self._state.camera_token = token
        if self._state.engine is not None:
            self._state.engine.set_camera_id(camera_id)
        self._open_violations.clear()
        self._state.monitor.set_active_alerts([])
        self._show_notice("Nenhuma camera selecionada")

    def _show_notice(self, text: str):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, text[:48], (24, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 230, 236), 2)
        self._state.update_frame(frame)

    def _apply_switch(self, capture: Optional[VideoCapture], tracker: PersonTracker, pending: tuple):
        source, camera_id, label, token = pending
        previous = (self._source, self._camera_id, self._state.camera_label)
        if source is None:
            if capture is not None:
                capture.stop()
            self._release_camera(camera_id, label, token)
            tracker.reset()
            print("[pipeline] Nenhuma câmera selecionada.")
            return None
        self._show_notice("Conectando camera...")
        if capture is not None:
            capture.stop()
        try:
            opened = VideoCapture(source)
            opened.start()
        except ConnectionError as exc:
            print(f"[pipeline] Falha ao abrir {source!r}: {exc}")
            self._state.camera_error = str(exc)
            self._state.camera_status = "error"
            self._state.camera_token = token
            if previous[0] is None:
                error = self._state.camera_error
                self._release_camera(previous[1], previous[2], token)
                self._state.camera_error = error
                return None
            try:
                restored = VideoCapture(previous[0])
                restored.start()
            except ConnectionError:
                return None
            self._source, self._camera_id = previous[0], previous[1]
            self._state.camera_source = previous[0]
            self._state.camera_id = previous[1]
            self._state.camera_label = previous[2]
            self._state.camera_status = "live"
            return restored
        self._source = source
        self._camera_id = camera_id
        self._state.camera_source = source
        self._state.camera_id = camera_id
        self._state.camera_label = label
        self._state.camera_error = None
        self._state.camera_status = "live"
        self._state.camera_token = token
        if self._state.engine is not None:
            self._state.engine.set_camera_id(camera_id)
        tracker.reset()
        self._open_violations.clear()
        self._state.monitor.set_active_alerts([])
        print(f"[pipeline] Câmera ativa: {camera_id} ← {source!r}")
        return opened

    def run(self):
        self._running = True
        capture: Optional[VideoCapture] = None
        try:
            capture = VideoCapture(self._source)
            capture.start()
            self._state.camera_status = "live"
            self._state.camera_error = None
        except ConnectionError as exc:
            print(f"[pipeline] ERRO ao conectar câmera: {exc}")
            self._state.camera_error = str(exc)
            self._state.camera_status = "error"
            capture = None

        try:
            self._run_loop(capture)
        except Exception as exc:
            print(f"[pipeline] ERRO durante o processamento: {exc}")
            traceback.print_exc()
        finally:
            if capture is not None:
                capture.stop()
            if self._show_window:
                cv2.destroyAllWindows()
            print(f"[pipeline] {self._camera_id} encerrado.")

    def _run_loop(self, capture: Optional[VideoCapture]):
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

        while self._running:
            pending = self._take_switch()
            if pending is not None:
                capture = self._apply_switch(capture, tracker, pending)
            if capture is None or not capture.is_running():
                time.sleep(0.1)
                continue

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

            required_now = list(self._state.required_ppe)
            for person in persons:
                owned = associations.get(person.track_id, [])
                for required in required_now:
                    if required in owned:
                        self._state.engine.clear_violation(person.track_id, required)
                        continue
                    self._state.engine.evaluate(
                        person_id=person.track_id,
                        missing_ppe=required,
                        threshold=self._state.confirm_frames,
                    )
                    alert = self._state.engine.get_pending_alert(person.track_id)
                    if alert is not None and alert.ppe_type == required:
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

            # A tela mostra só o que ainda falta neste quadro.
            self._state.monitor.set_active_alerts(violations)

            fresh = []
            current_keys = set()
            for v in violations:
                kind = v.reason[4:] if str(v.reason).startswith("sem ") else v.reason
                key = (v.person_id, kind)
                current_keys.add(key)
                if key not in self._open_violations:
                    fresh.append(v)
            self._open_violations = current_keys

            if fresh and self._state.engine is not None:
                self._state.engine.process_alerts()
                for v in fresh:
                    img_path = recorder.save_image(frame, v)
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

    def stop(self):
        self._running = False
