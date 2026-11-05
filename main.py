#!/usr/bin/env python3
"""PPE Detection – ponto de entrada CLI + Dashboard web.

Exemplos de uso:
  python main.py                                   # câmera USB padrão
  python main.py --camera 0 --show-window          # com janela OpenCV
  python main.py --camera rtsp://192.168.1.10/live # câmera RTSP
  python main.py --camera 0 --ppe-model models/ppe.pt --required-ppe helmet vest
  python main.py --no-web --show-window            # só janela, sem Flask
"""
import argparse
import os
import sys
import threading
import time

# Garante que src/ seja importável sem instalar o pacote
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sistema de detecção de EPIs com dashboard web.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Câmera
    p.add_argument("--camera", default="0",
                   metavar="SRC",
                   help="Fonte de vídeo: índice USB (0, 1…) ou URL RTSP")
    p.add_argument("--camera-id", default="CAM-01",
                   metavar="ID",
                   help="Identificador da câmera no sistema")

    # Modelo de IA
    p.add_argument("--ppe-model", default=None,
                   metavar="PATH",
                   help="Caminho para modelo .pt de EPIs (deixe vazio para usar só rastreamento)")
    p.add_argument("--confidence", type=float, default=0.5,
                   metavar="0-1",
                   help="Limiar de confiança mínima para detecções")

    # Regras
    p.add_argument("--required-ppe", nargs="+",
                   default=["helmet", "vest", "glasses"],
                   metavar="EPI",
                   help="EPIs obrigatórios (ex: helmet vest glasses)")
    p.add_argument("--confirm-frames", type=int, default=5,
                   metavar="N",
                   help="Quadros consecutivos sem EPI antes de emitir alerta")
    p.add_argument("--fps", type=int, default=15,
                   metavar="FPS",
                   help="Taxa mínima de processamento de quadros")

    # Evidências
    p.add_argument("--pre-seconds", type=int, default=10,
                   help="Segundos de vídeo capturados antes do alerta")
    p.add_argument("--post-seconds", type=int, default=5,
                   help="Segundos de vídeo capturados após o alerta")

    # Dashboard web
    p.add_argument("--host", default="0.0.0.0",
                   help="Host do dashboard web")
    p.add_argument("--port", type=int, default=5000,
                   help="Porta do dashboard web")
    p.add_argument("--no-web", action="store_true",
                   help="Desabilita o dashboard web")

    # Saída
    p.add_argument("--show-window", action="store_true",
                   help="Exibe janela OpenCV com o vídeo anotado em tempo real")

    return p.parse_args()


def main():
    args = _parse_args()

    # Converte source para int se for um índice numérico
    source = int(args.camera) if args.camera.isdigit() else args.camera

    from src.dashboard.state import AppState
    from src.dashboard.pipeline import CameraPipeline

    # ── Estado compartilhado ─────────────────────────────────────────────
    state = AppState()
    from src.video.devices import label_for_source

    state.setup(
        camera_id=args.camera_id,
        required_ppe=args.required_ppe,
        confirm_frames=args.confirm_frames,
        pre_seconds=args.pre_seconds,
        post_seconds=args.post_seconds,
    )
    state.camera_source = source
    state.camera_label = label_for_source(source)

    # ── Pipeline de vídeo (thread separada) ──────────────────────────────
    pipeline = CameraPipeline(
        source=source,
        camera_id=args.camera_id,
        ppe_model=args.ppe_model,
        confidence=args.confidence,
        min_fps=args.fps,
        show_window=args.show_window,
        state=state,
    )
    state.attach_pipeline(pipeline)
    t = threading.Thread(target=pipeline.run, daemon=True)
    t.start()
    print(f"[ppe] Câmera '{args.camera_id}' iniciada  →  fonte: {source!r}")
    print(f"[ppe] EPIs obrigatórios: {args.required_ppe}")
    if args.ppe_model:
        print(f"[ppe] Modelo EPI: {args.ppe_model}")
    else:
        print("[ppe] Sem modelo EPI — apenas rastreamento de pessoas ativo.")

    # ── Dashboard web ────────────────────────────────────────────────────
    if args.no_web:
        print("[ppe] Dashboard desabilitado. Pressione Ctrl+C para encerrar.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        from src.dashboard.app import create_app
        app = create_app(state)
        url = f"http://localhost:{args.port}"
        print(f"[ppe] Dashboard disponível em  →  {url}")
        try:
            app.run(host=args.host, port=args.port, debug=False, threaded=True)
        except KeyboardInterrupt:
            pass

    pipeline.stop()
    print("[ppe] Sistema encerrado.")


if __name__ == "__main__":
    main()
