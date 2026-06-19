"""Menu interativo de seleção de EPIs."""

from __future__ import annotations

import sys

from ppe_detection.domain.ppe import PPE_CATALOG


def select_ppe_interactive(preselected: list[str] | None = None) -> list[str]:
    selected: set[str] = set(preselected or ["helmet", "vest"])

    reset = "\033[0m"
    bold = "\033[1m"
    green = "\033[32m"
    cyan = "\033[36m"
    yellow = "\033[33m"
    dim = "\033[2m"

    def render() -> None:
        print("\033[H\033[J", end="")
        print(f"{bold}╔══════════════════════════════════════════╗{reset}")
        print(f"{bold}║       Seleção de EPIs Obrigatórios       ║{reset}")
        print(f"{bold}╚══════════════════════════════════════════╝{reset}")
        print()
        print(f"  {dim}Use o número para marcar/desmarcar.{reset}")
        print(f"  {dim}Pressione {bold}Enter{reset}{dim} para confirmar e iniciar.{reset}")
        print()

        for i, ppe in enumerate(PPE_CATALOG, start=1):
            is_on = ppe.key in selected
            marker = f"{green}[✓]{reset}" if is_on else "[ ]"
            label = f"{bold}{ppe.label}{reset}" if is_on else ppe.label
            print(f"  {marker}  {i}. {ppe.icon} {label:12s}  {dim}{ppe.description}{reset}")

        print()
        names = [p.label for p in PPE_CATALOG if p.key in selected]
        if names:
            print(f"  {cyan}Selecionados:{reset} {bold}{', '.join(names)}{reset}")
        else:
            print(f"  {yellow}Nenhum EPI selecionado — sem alertas.{reset}")
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
                key = PPE_CATALOG[idx].key
                selected.symmetric_difference_update({key})

    print("\033[H\033[J", end="")
    return [p.key for p in PPE_CATALOG if p.key in selected]
