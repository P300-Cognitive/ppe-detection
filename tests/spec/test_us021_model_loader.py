"""Testes do carregador de modelo."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ppe_detection.detection.model_loader import resolve_model_path


@pytest.mark.spec("US-021")
class TestModelLoader:
    def test_local_path_unchanged(self):
        assert resolve_model_path("models/best.pt") == "models/best.pt"

    def test_hf_uri_downloads(self):
        with patch("huggingface_hub.hf_hub_download", return_value="/cache/best.pt") as mock:
            result = resolve_model_path("hf://Hexmon/vyra-yolo-ppe-detection/best.pt")
        assert result == "/cache/best.pt"
        mock.assert_called_once_with(
            repo_id="Hexmon/vyra-yolo-ppe-detection",
            filename="best.pt",
        )

    def test_hf_uri_single_slash(self):
        with patch("huggingface_hub.hf_hub_download", return_value="/cache/best.pt") as mock:
            result = resolve_model_path("hf:/Hexmon/vyra-yolo-ppe-detection/best.pt")
        assert result == "/cache/best.pt"
        mock.assert_called_once_with(
            repo_id="Hexmon/vyra-yolo-ppe-detection",
            filename="best.pt",
        )
