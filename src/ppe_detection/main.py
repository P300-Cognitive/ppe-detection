from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ppe_detection.cli.selector import select_ppe_interactive
from ppe_detection.config import load_config
from ppe_detection.domain.ppe import PPE_CATALOG, PPE_KEYS, ppe_label
from ppe_detection.pipeline import PPEPipeline


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _add_ppe_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--required-ppe", nargs="+", choices=sorted(PPE_KEYS), metavar="EPI",
        help="EPIs obrigatórios. Se omitido, abre menu interativo.",
    )


def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", "-s", help="Fonte de vídeo: USB ou RTSP")
    parser.add_argument("--config", "-c", type=Path, help="Arquivo de configuração YAML")
    parser.add_argument("--model", "-m", help="Modelo YOLO (.pt)")
    parser.add_argument("--confidence", type=float, help="Limiar de confiança (0-1)")
    _add_ppe_args(parser)
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
    if args.save_evidence:
        config.evidence.enabled = True
    return config


def _resolve_required_ppe(args, config) -> list[str]:
    if args.required_ppe:
        return args.required_ppe
    return select_ppe_interactive(config.rules.required_ppe)


def cmd_run(args) -> int:
    config = _apply_config(args, load_config(args.config))
    config.rules.required_ppe = _resolve_required_ppe(args, config)

    labels = [ppe_label(k) for k in config.rules.required_ppe]
    logging.info("EPIs obrigatórios: %s", ", ".join(labels) or "nenhum")

    try:
        PPEPipeline(config).run(show=not args.no_display)
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário.")
    except Exception:
        logging.exception("Erro fatal no pipeline.")
        return 1
    return 0


def cmd_select(_args) -> int:
    print(" ".join(select_ppe_interactive()))
    return 0


def cmd_dashboard(args) -> int:
    import uvicorn
    from ppe_detection.dashboard.app import create_app

    config = _apply_config(args, load_config(args.config))
    if args.port:
        config.dashboard.port = args.port
    if args.host:
        config.dashboard.host = args.host
    config.rules.required_ppe = _resolve_required_ppe(args, config)

    labels = [ppe_label(k) for k in config.rules.required_ppe]
    logging.info("Dashboard — EPIs monitorados: %s", ", ".join(labels) or "nenhum")
    logging.info("Acesse: http://%s:%s/dashboard/", config.dashboard.host, config.dashboard.port)

    uvicorn.run(create_app(config), host=config.dashboard.host, port=config.dashboard.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detector de EPI em tempo real (YOLO + Spec-Driven Design)",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Iniciar detector")
    _add_run_args(run_p)
    run_p.set_defaults(func=cmd_run)

    sel_p = sub.add_parser("select", help="Selecionar EPIs interativamente")
    sel_p.set_defaults(func=cmd_select)

    dash_p = sub.add_parser("dashboard", help="Painel multi-câmera")
    dash_p.add_argument("--config", "-c", type=Path)
    dash_p.add_argument("--model", "-m", help="Modelo YOLO (.pt)")
    dash_p.add_argument("--confidence", type=float, help="Limiar de confiança (0-1)")
    _add_ppe_args(dash_p)
    dash_p.add_argument("--host")
    dash_p.add_argument("--port", type=int)
    dash_p.add_argument("--save-evidence", action="store_true")
    dash_p.add_argument("--verbose", "-v", action="store_true")
    dash_p.set_defaults(func=cmd_dashboard)

    _add_run_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(getattr(args, "verbose", False))

    if args.command is None:
        if any([
            getattr(args, "source", None),
            getattr(args, "config", None),
            getattr(args, "model", None),
            getattr(args, "no_display", False),
            getattr(args, "save_evidence", False),
        ]):
            return cmd_run(args)
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
