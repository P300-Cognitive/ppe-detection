#!/usr/bin/env python3
"""Baixa o modelo PPE padrão do HuggingFace para uso offline."""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import hf_hub_download


DEFAULT_REPO = "Hexmon/vyra-yolo-ppe-detection"
DEFAULT_FILE = "best.pt"


def download_model(output_dir: Path, repo: str, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = hf_hub_download(
        repo_id=repo,
        filename=filename,
        local_dir=str(output_dir),
    )
    return Path(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa modelo YOLO de EPI")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("models"),
        help="Diretório de destino",
    )
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--file", default=DEFAULT_FILE)
    args = parser.parse_args()

    path = download_model(args.output, args.repo, args.file)
    print(f"Modelo salvo em: {path}")
    print(f"Use: ppe-detection --model {path}")


if __name__ == "__main__":
    main()
