from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ppe_detection.config import load_config
from ppe_detection.pipeline import PPEPipeline

# ---------------------------------------------------------------------------
# Catálogo de EPIs disponíveis
# ---------------------------------------------------------------------------
PPE_CATALOG: list[dict] = [
    {
        "key": "helmet",
        "label": "Capacete",
        "description": "Hardhat / capacete de segurança",
        "icon": "⛑️ ",
    },
    {
        "key": "vest",
        "label": "Colete",
        "description": "Colete refletivo / alta visibilidade",
        "icon": "🦺",
    },
    {
        "key": "gloves",
        "label": "Luvas",
        "description": "Luvas de proteção",
        "icon": "🧤",
    },
    {
        "key": "goggles",
        "label": "Oculos",
        "description": "Óculos de proteção / goggles",
        "icon": "🥽",
    },
    {
        "key": "mask",
        "label": "Mascara",
        "description": "Máscara / respirador",
        "icon": "😷",
    },
    {
        "key": "boots",
        "label": "Botas",
        "description": "Botas de segurança",
        "icon": "🥾",
    },
]


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Menu interativo de seleção de EPIs
# ---------------------------------------------------------------------------

def _clear_line() -> None:
    print("\r\033[K", end="")


def select_ppe_interactive(preselected: list[str] | None = None) -> list[str]:
    """Menu de seleção interativa de EPIs obrigatórios."""
    selected: set[str] = set(preselected or ["helmet", "vest"])

    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[32m"
    CYAN   = "\033[36m"
    YELLOW = "\033[33m"
    DIM    = "\033[2m"

    def render() -> None:
        print("\033[H\033[J", end="")  # limpa tela
        print(f"{BOLD}╔══════════════════════════════════════════╗{RESET}")
        print(f"{BOLD}║       Seleção de EPIs Obrigatórios       ║{RESET}")
        print(f"{BOLD}╚══════════════════════════════════════════╝{RESET}")
        print()
        print(f"  {DIM}Use o número para marcar/desmarcar.{RESET}")
        print(f"  {DIM}Pressione {BOLD}Enter{RESET}{DIM} para confirmar e iniciar.{RESET}")
        print()
        for i, ppe in enumerate(PPE_CATALOG, start=1):
            is_on = ppe["key"] in selected
            marker = f"{GREEN}[✓]{RESET}" if is_on else f"[ ]"
            icon   = ppe["icon"]
            label  = f"{BOLD}{ppe['label']}{RESET}" if is_on else ppe["label"]
            desc   = f"{DIM}{ppe['description']}{RESET}"
            print(f"  {marker}  {i}. {icon} {label:12s}  {desc}")
        print()

        names = [PPE_CATALOG[k]["label"] for k, p in enumerate(PPE_CATALOG) if p["key"] in selected]
        if names:
            print(f"  {CYAN}Selecionados:{RESET} {BOLD}{', '.join(names)}{RESET}")
        else:
            print(f"  {YELLOW}Nenhum EPI selecionado — o sistema só monitorará sem alertas.{RESET}")
        print()

    while True:
        render()
        try:
            raw = input("  Número (1-6) ou Enter para iniciar: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            sys.exit(0)

        if raw == "":
            break

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(PPE_CATALOG):
                key = PPE_CATALOG[idx]["key"]
                if key in selected:
                    selected.discard(key)
                else:
                    selected.add(key)
            else:
                pass  # número inválido — só re-renderiza
        # qualquer outra entrada → re-renderiza

    print("\033[H\033[J", end="")  # limpa tela antes de iniciar
    return [p["key"] for p in PPE_CATALOG if p["key"] in selected]


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def _add_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", "-s", help="Fonte de vídeo: USB ou RTSP")
    parser.add_argument("--config", "-c", type=Path, help="Arquivo de configuração YAML")
    parser.add_argument("--model", "-m", help="Modelo YOLO (.pt)")
    parser.add_argument("--confidence", type=float, help="Limiar de confiança (0-1)")
    parser.add_argument(
        "--required-ppe", nargs="+",
        choices=[p["key"] for p in PPE_CATALOG],
        metavar="EPI",
        help="EPIs obrigatórios. Se omitido, abre menu interativo.",
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
    if args.save_evidence:
        config.evidence.enabled = True
    return config


def cmd_run(args) -> int:
    config = _apply_config(args, load_config(args.config))

    if args.required_ppe:
        config.rules.required_ppe = args.required_ppe
    else:
        # Nenhum EPI especificado → abre menu interativo
        config.rules.required_ppe = select_ppe_interactive(config.rules.required_ppe)

    selected_labels = [
        next(p["label"] for p in PPE_CATALOG if p["key"] == k)
        for k in config.rules.required_ppe
    ]
    logging.info("EPIs obrigatórios: %s", ", ".join(selected_labels) or "nenhum")

    try:
        PPEPipeline(config).run(show=not args.no_display)
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário.")
    except Exception:
        logging.exception("Erro fatal no pipeline.")
        return 1
    return 0


def cmd_select(args) -> int:
    """Abre o menu e imprime os EPIs selecionados (útil para scripts)."""
    selected = select_ppe_interactive()
    print(" ".join(selected))
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


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detector de EPI em tempo real (YOLO + Spec-Driven Design)",
    )
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Iniciar detector (abre menu se nenhum EPI for passado)")
    _add_run_args(run_p)
    run_p.set_defaults(func=cmd_run)

    sel_p = sub.add_parser("select", help="Selecionar EPIs interativamente e imprimir resultado")
    sel_p.set_defaults(func=cmd_select)

    dash_p = sub.add_parser("dashboard", help="Painel multi-câmera")
    dash_p.add_argument("--config", "-c", type=Path)
    dash_p.add_argument("--host")
    dash_p.add_argument("--port", type=int)
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
