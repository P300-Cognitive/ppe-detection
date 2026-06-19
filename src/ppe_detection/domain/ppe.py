"""Catálogo e utilitários de EPI — fonte única de verdade."""

from __future__ import annotations

from dataclasses import dataclass

from ppe_detection.config import AppConfig, ClassConfig
from ppe_detection.domain.geometry import iou
from ppe_detection.domain.models import BoundingBox, FrameDetections


@dataclass(frozen=True)
class PPEType:
    key: str
    label: str
    description: str
    icon: str


PPE_CATALOG: tuple[PPEType, ...] = (
    PPEType("helmet", "Capacete", "Hardhat / capacete de segurança", "⛑️ "),
    PPEType("vest", "Colete", "Colete refletivo / alta visibilidade", "🦺"),
    PPEType("gloves", "Luvas", "Luvas de proteção", "🧤"),
    PPEType("goggles", "Oculos", "Óculos de proteção / goggles", "🥽"),
    PPEType("mask", "Mascara", "Máscara / respirador", "😷"),
    PPEType("boots", "Botas", "Botas de segurança", "🥾"),
)

PPE_KEYS: frozenset[str] = frozenset(p.key for p in PPE_CATALOG)

# Labels de violação do modelo → chave canônica de EPI
VIOLATION_LABEL_TO_PPE: dict[str, str] = {
    "NO-Hardhat": "helmet",
    "NO-Safety Vest": "vest",
    "NO-Gloves": "gloves",
    "NO-Goggles": "goggles",
    "NO-Mask": "mask",
}

DISPLAY_LABELS: dict[str, str] = {p.key: p.label for p in PPE_CATALOG}


def ppe_label(key: str) -> str:
    return DISPLAY_LABELS.get(key, key)


def violation_to_ppe_key(label: str, classes: ClassConfig | None = None) -> str | None:
    """Converte label de violação (ex: NO-Hardhat) → chave de EPI (ex: helmet)."""
    if label in VIOLATION_LABEL_TO_PPE:
        return VIOLATION_LABEL_TO_PPE[label]

    if classes:
        for ppe_key, labels in classes.violation.items():
            if label in labels:
                return ppe_key.removeprefix("no_")

    if label.startswith("NO-"):
        return (
            label.removeprefix("NO-")
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )
    return None


def ppe_key_from_detection_label(label: str, classes: ClassConfig) -> str | None:
    """Converte label positivo de EPI (ex: Hardhat) → chave canônica."""
    mapping = {
        "helmet": classes.helmet,
        "vest": classes.vest,
        "gloves": classes.gloves,
        "goggles": classes.goggles,
        "mask": classes.mask,
        "boots": classes.boots,
    }
    for key, labels in mapping.items():
        if label in labels:
            return key
    return None


def is_required_ppe(label: str, required: set[str], classes: ClassConfig) -> bool:
    """True se o label (positivo ou violação) pertence a um EPI obrigatório."""
    ppe_key = violation_to_ppe_key(label, classes)
    if ppe_key:
        return ppe_key in required
    ppe_key = ppe_key_from_detection_label(label, classes)
    return ppe_key in required if ppe_key else False


def relevant_violations(
    detections: FrameDetections,
    required_ppe: list[str],
    classes: ClassConfig,
) -> list[BoundingBox]:
    required = set(required_ppe)
    return [
        v for v in detections.violations
        if (key := violation_to_ppe_key(v.label, classes)) and key in required
    ]


def relevant_ppe_items(
    detections: FrameDetections,
    required_ppe: list[str],
    classes: ClassConfig,
) -> list[BoundingBox]:
    required = set(required_ppe)
    result: list[BoundingBox] = []
    for item in detections.ppe_items:
        key = ppe_key_from_detection_label(item.label, classes)
        if key and key in required:
            result.append(item)
    return result


def count_people(
    detections: FrameDetections,
    required_ppe: list[str],
    classes: ClassConfig,
) -> int:
    """Conta pessoas visíveis, deduplicando violações sobrepostas."""
    if detections.persons:
        track_ids = {p.track_id for p in detections.persons if p.track_id is not None}
        untracked = sum(1 for p in detections.persons if p.track_id is None)
        return len(track_ids) + untracked

    violations = relevant_violations(detections, required_ppe, classes)
    if not violations:
        return 0

    return _count_violation_groups(violations)


def _count_violation_groups(violations: list[BoundingBox]) -> int:
    """Agrupa violações sobrepostas como uma única pessoa."""
    track_ids = {v.track_id for v in violations if v.track_id is not None}
    untracked = [v for v in violations if v.track_id is None]

    groups = len(track_ids)
    assigned: set[int] = set()

    for i, box in enumerate(untracked):
        if i in assigned:
            continue
        groups += 1
        for j, other in enumerate(untracked):
            if j <= i or j in assigned:
                continue
            if iou(box, other) > 0.2:
                assigned.add(j)

    return groups
