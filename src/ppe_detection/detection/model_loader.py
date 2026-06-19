"""Resolução de caminhos de modelo — suporta HuggingFace e arquivos locais."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_model_path(path: str) -> str:
    """Converte URI hf:// para arquivo local; demais caminhos passam direto."""
    if not path.startswith(("hf://", "hf:/")):
        return path

    uri = path.removeprefix("hf://").removeprefix("hf:/")
    if "/" not in uri:
        raise ValueError(f"URI HuggingFace inválida: {path}")

    repo_id, filename = uri.rsplit("/", 1)
    from huggingface_hub import hf_hub_download

    logger.info("Baixando modelo %s/%s do HuggingFace...", repo_id, filename)
    local_path = hf_hub_download(repo_id=repo_id, filename=filename)
    logger.info("Modelo disponível em: %s", local_path)
    return local_path


def ensure_local_model(path: str, cache_dir: Path | None = None) -> str:
    """Resolve o path e verifica que o arquivo existe."""
    resolved = resolve_model_path(path)
    if not Path(resolved).exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {resolved}. "
            f"Execute: python scripts/download_model.py"
        )
    return resolved
