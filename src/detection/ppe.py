"""Detecção de EPIs em frames usando YOLOv8 com modelo customizado."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
from ultralytics import YOLO, YOLOWorld

from src.core.models import Detection

# Mapeamento padrão de nome de classe → índice no modelo PPE.
# Substituir conforme as classes do modelo treinado.
DEFAULT_CLASS_LABELS: Dict[str, int] = {
    "helmet":  0,
    "vest":    1,
    "glasses": 2,
    "mask":    3,
    "gloves":  4,
    "boots":   5,
}

# Nomes que o modelo pode usar para cada EPI interno.
_CLASS_ALIASES: Dict[str, set[str]] = {
    "helmet":  {"helmet", "hardhat", "hard hat", "safety helmet"},
    "vest":    {"vest", "safety vest", "reflective vest"},
    "glasses": {"glasses", "goggles", "safety glasses", "safety goggles", "eyeglasses"},
    "mask":    {"mask", "face mask"},
    "gloves":  {"gloves", "glove", "safety gloves"},
    "boots":   {"boots", "safety boots"},
}

# YOLO-World cobre o close da webcam. O modelo de canteiro não é carregado por padrão.
_OPEN_VOCAB_PROMPTS: Dict[str, List[str]] = {
    "helmet": ["helmet", "safety helmet", "hard hat"],
    "glasses": [
        "safety glasses",
        "safety goggles",
        "goggles",
        "protective eyewear",
        "eyeglasses",
        "glasses",
    ],
}
_OPEN_VOCAB_CONFIDENCE = {
    "helmet": 0.20,
    "glasses": 0.12,
}

_RENDER_COLOR = (0, 255, 0)   # BGR verde para EPIs detectados
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _open_vocab_prompt_list() -> tuple[List[str], List[str]]:
    prompts: List[str] = []
    owners: List[str] = []
    for class_name, group in _OPEN_VOCAB_PROMPTS.items():
        for prompt in group:
            prompts.append(prompt)
            owners.append(class_name)
    return prompts, owners


def _load_open_vocab_model() -> tuple[YOLOWorld, List[str]]:
    """Abre o YOLO-World com os prompts de capacete e óculos."""
    import ultralytics.nn.text_model as text_model

    text_model.WEIGHTS_DIR = _REPO_ROOT / "weights"
    weights = _REPO_ROOT / "weights" / "yolov8s-worldv2.pt"
    prompts, owners = _open_vocab_prompt_list()
    model = YOLOWorld(str(weights) if weights.is_file() else "yolov8s-worldv2.pt")
    model.set_classes(prompts)
    return model, owners


class PPEDetector:
    """Detecta EPIs num frame BGR.

    model_path: caminho para o modelo .pt treinado em EPIs.
                Capacete e óculos são detectados mesmo sem esse modelo.
    classes:    lista de nomes de classe a detectar (ex: ['helmet', 'vest']).
    """

    def __init__(
        self,
        classes: List[str],
        model_path: Optional[str] = None,
        confidence: float = 0.5,
        class_labels: Optional[Dict[str, int]] = None,
    ):
        self._classes = classes
        self._confidence = confidence
        self._class_labels = class_labels or DEFAULT_CLASS_LABELS
        self._idx_to_name = {v: k for k, v in self._class_labels.items()}
        self._model: Optional[YOLO] = YOLO(model_path) if model_path else None
        self._open_vocab_model: Optional[YOLOWorld] = None
        self._open_vocab_owners: List[str] = []

    def detect(self, frame: np.ndarray) -> List[Detection]:
        detections: List[Detection] = []
        if self._model is not None:
            detections.extend(self._detect_with_model(frame))
        if any(class_name in _OPEN_VOCAB_PROMPTS for class_name in self._classes):
            detections.extend(self._detect_open_vocab(frame))
        return detections

    def _detect_with_model(self, frame: np.ndarray) -> List[Detection]:
        names = {int(i): str(n) for i, n in self._model.names.items()}
        indices = self._indices_for(names)
        if not indices:
            return []
        results = self._model(frame, classes=indices, conf=self._confidence, verbose=False)
        detections: List[Detection] = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                cls_idx = int(box.cls[0])
                detections.append(
                    Detection(
                        class_name=self._canonical_name(names.get(cls_idx, ""), cls_idx),
                        confidence=float(box.conf[0]),
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return detections

    def _indices_for(self, names: Dict[int, str]) -> List[int]:
        indices: List[int] = []
        for class_name in self._classes:
            if class_name in _OPEN_VOCAB_PROMPTS:
                continue
            aliases = _CLASS_ALIASES.get(class_name, {class_name})
            matched = [
                i for i, name in names.items()
                if name.lower() in aliases and not name.lower().startswith("no")
            ]
            if matched:
                indices.extend(matched)
                continue
            fallback = self._class_labels.get(class_name)
            label = names.get(fallback, "").lower() if fallback is not None else ""
            if fallback is not None and (label in aliases or label == class_name):
                indices.append(fallback)
        return sorted(set(indices))

    def _canonical_name(self, raw_name: str, cls_idx: int) -> str:
        label = raw_name.lower()
        for class_name, aliases in _CLASS_ALIASES.items():
            if label in aliases:
                return class_name
        return self._idx_to_name.get(cls_idx, raw_name or str(cls_idx))

    def _detect_open_vocab(self, frame: np.ndarray) -> List[Detection]:
        model = self._open_vocab_model
        if model is None:
            model, owners = _load_open_vocab_model()
            self._open_vocab_model = model
            self._open_vocab_owners = owners
        floor = min(_OPEN_VOCAB_CONFIDENCE[c] for c in self._classes if c in _OPEN_VOCAB_CONFIDENCE)
        confidence = min(self._confidence, floor)
        results = model(frame, conf=confidence, verbose=False)
        detections: List[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_idx = int(box.cls[0])
                class_name = self._open_vocab_owners[cls_idx]
                if class_name not in self._classes:
                    continue
                score = float(box.conf[0])
                if score < min(self._confidence, _OPEN_VOCAB_CONFIDENCE[class_name]):
                    continue
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                detections.append(
                    Detection(
                        class_name=class_name,
                        confidence=score,
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return detections

    def render(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        annotated = frame.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), _RENDER_COLOR, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(
                annotated, label, (x1, max(y1 - 6, 0)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, _RENDER_COLOR, 1,
            )
        return annotated
