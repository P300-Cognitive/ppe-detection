"""Gerenciamento de modelos de IA: upload, validação e troca a quente."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from src.core.models import AIModel

_VALID_EXTENSIONS = {".pt", ".onnx", ".tflite"}


class ModelManager:
    """Gerencia modelos treinados: armazena, lista e ativa sem reiniciar o sistema."""

    def __init__(self, models_dir: str = "models"):
        self._models_dir = Path(models_dir)
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._models: Dict[str, AIModel] = {}
        self._active_id: Optional[str] = None
        self._running = True  # permanece True até stop() ser chamado

    def upload(self, file_path: str) -> AIModel:
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        if src.suffix.lower() not in _VALID_EXTENSIONS:
            raise ValueError(
                f"Extensão inválida '{src.suffix}'. "
                f"Aceitas: {', '.join(sorted(_VALID_EXTENSIONS))}"
            )
        model_id = uuid.uuid4().hex[:8]
        dest = self._models_dir / f"{model_id}{src.suffix}"
        shutil.copy2(str(src), str(dest))
        model = AIModel(id=model_id, path=str(dest), is_active=False)
        self._models[model_id] = model
        return model

    def list_available(self) -> List[AIModel]:
        return list(self._models.values())

    def activate(self, model_id: str):
        if model_id not in self._models:
            raise KeyError(f"Modelo '{model_id}' não encontrado")
        if self._active_id and self._active_id in self._models:
            self._models[self._active_id].is_active = False
        self._models[model_id].is_active = True
        self._active_id = model_id

    def get_active(self) -> Optional[AIModel]:
        return self._models.get(self._active_id) if self._active_id else None

    def is_running(self) -> bool:
        return self._running

    def stop(self):
        self._running = False
