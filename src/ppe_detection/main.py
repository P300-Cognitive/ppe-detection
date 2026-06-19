from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ppe_detection.config import load_config
from ppe_detection.pipeline import PPEPipeline


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", "-s", help="Fonte de vídeo: USB ou RTSP")
    parser.add_argument("--config", "-c", type=Path, help="Arquivo de configuração YAML")
    parser.add_argument("--model", "-m", help="Modelo YOLO (.pt)")
    parser.add_argument("--confidence", type=float, help="Limiar de confiança (0-1)")
    parser.add_argument(
        "--required-ppe", nargs="+",
        choices=["helmet", "vest", "gloves", "goggles", "mask", "boots"],
    )
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--save-evidence", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")


def _apply_config(args, config):
    if args.source:
        config.camera.source = args.source
    if args.model:
        config.model.path = args.model
    if args.confidence is not None:
        config.model.confidence = args.confidence
    if args.required_ppe:
        config.rules.required_ppe = args.required_ppe
    if args.save_evidence:
        config.evidence.enabled = True
    return config


def cmd_run(args) -> int:
    config = _apply_config(args, load_config(args.config))
    try:
        PPEPipeline(config).run(show=not args.no_display)
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário.")
    except Exception:
        logging.exception("Erro fatal no pipeline.")
        return 1
    return 0


def cmd_dashboard(args) -> int:
    import uvicorn
    from ppe_detection.dashboard.app import create_app

    config = load_config(args.config)
    if args.port:
        config.dashboard.port = args.port
    if args.host:
        config.dashboard.host = args.host
    if args.save_evidence:
        config.evidence.enabled = True

    app = create_app(config)
    uvicorn.run(app, host=config.dashboard.host, port=config.dashboard.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detector de EPI (YOLO + SDD)")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Executar detector em uma câmera")
    _add_run_args(run_p)
    run_p.set_defaults(func=cmd_run)

    dash_p = sub.add_parser("dashboard", help="Painel multi-câmera (US-017)")
    dash_p.add_argument("--config", "-c", type=Path)
    dash_p.add_argument("--host", help="Host do servidor")
    dash_p.add_argument("--port", type=int, help="Porta do servidor")
    dash_p.add_argument("--save-evidence", action="store_true")
    dash_p.add_argument("--verbose", "-v", action="store_true")
    dash_p.set_defaults(func=cmd_dashboard)

    # Compatibilidade: flags diretas invocam "run"
    _add_run_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))

    if args.command is None:
        # Modo legado: ppe-detection --source 0
        if any([args.source, args.config, args.model, args.no_display, args.save_evidence]):
            return cmd_run(args)
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
