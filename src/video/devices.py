"""Câmeras locais visíveis pelo sistema e leitura do endereço escolhido na tela."""
from __future__ import annotations

from pathlib import Path


def list_local_cameras() -> list[dict]:
    """Lista nós de captura V4L2 sem abrir o dispositivo que já está em uso."""
    root = Path("/sys/class/video4linux")
    if not root.is_dir():
        return []
    nodes: list[tuple[int, Path]] = []
    for node in root.iterdir():
        suffix = node.name[5:]
        if node.name.startswith("video") and suffix.isdigit():
            nodes.append((int(suffix), node))
    devices = []
    for index, node in sorted(nodes):
        index_file = node / "index"
        try:
            if index_file.is_file() and index_file.read_text().strip() != "0":
                continue
            name_file = node / "name"
            name = name_file.read_text().strip() if name_file.is_file() else f"Câmera {index}"
        except OSError:
            continue
        devices.append({
            "id": f"USB-{index}",
            "source": str(index),
            "label": f"{name} · USB {index}",
            "kind": "local",
        })
    return devices


def label_for_source(source: int | str) -> str:
    text = str(source)
    if text.isdigit():
        for device in list_local_cameras():
            if device["source"] == text:
                return device["label"]
        return f"USB {text}"
    return text


NO_CAMERA = "none"


def parse_source(raw: str) -> int | str | None:
    """Aceita o índice USB, um endereço rtsp/http ou nenhuma câmera."""
    text = str(raw).strip()
    if not text:
        raise ValueError("Informe a câmera.")
    if text.lower() == NO_CAMERA:
        return None
    if text.isdigit():
        return int(text)
    if "://" not in text:
        text = "rtsp://" + text
    if not text.lower().startswith(("rtsp://", "rtsps://", "http://", "https://")):
        raise ValueError("Use um endereço rtsp:// ou http://.")
    return text
