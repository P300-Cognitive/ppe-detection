from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CameraConfig:
    source: str = "0"
    width: int = 1280
    height: int = 720
    min_fps: int = 10
    reconnect_delay_sec: float = 3.0


@dataclass
class ModelConfig:
    path: str = "hf://Hexmon/vyra-yolo-ppe-detection/best.pt"
    confidence: float = 0.25
    device: str = ""


@dataclass
class ClassConfig:
    person: list[str] = field(default_factory=lambda: ["Person"])
    helmet: list[str] = field(default_factory=lambda: ["Hardhat"])
    vest: list[str] = field(default_factory=lambda: ["Safety Vest"])
    gloves: list[str] = field(default_factory=lambda: ["Gloves"])
    goggles: list[str] = field(default_factory=lambda: ["Goggles"])
    mask: list[str] = field(default_factory=lambda: ["Mask"])
    boots: list[str] = field(default_factory=list)
    violation: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class TrackingConfig:
    enabled: bool = True
    tracker: str = "bytetrack.yaml"


@dataclass
class RulesConfig:
    required_ppe: list[str] = field(default_factory=lambda: ["helmet", "vest"])
    confirmation_frames: int = 15


@dataclass
class DisplayConfig:
    show_confidence: bool = True
    alert_color: tuple[int, int, int] = (0, 0, 255)
    person_color: tuple[int, int, int] = (0, 255, 0)
    ppe_color: tuple[int, int, int] = (255, 200, 0)
    window_name: str = "PPE Detection"


@dataclass
class EvidenceConfig:
    enabled: bool = False
    output_dir: str = "evidence"
    save_on_alert: bool = True
    save_video: bool = True
    video_pre_seconds: float = 3.0
    video_post_seconds: float = 3.0
    video_fps: int = 10


@dataclass
class StorageConfig:
    db_path: str = "data/occurrences.db"
    reports_dir: str = "data/reports"


@dataclass
class DashboardConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    cameras_file: str = "config/cameras.yaml"


@dataclass
class CameraEntry:
    id: str
    name: str
    source: str


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    classes: ClassConfig = field(default_factory=ClassConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    rules: RulesConfig = field(default_factory=RulesConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    evidence: EvidenceConfig = field(default_factory=EvidenceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)


def _to_tuple_color(value: list[int] | tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(int(v) for v in value)  # type: ignore[return-value]


def _build_config(data: dict[str, Any]) -> AppConfig:
    camera = CameraConfig(**data.get("camera", {}))
    model = ModelConfig(**data.get("model", {}))

    classes_raw = data.get("classes", {})
    classes = ClassConfig(
        person=classes_raw.get("person", ["Person"]),
        helmet=classes_raw.get("helmet", ["Hardhat"]),
        vest=classes_raw.get("vest", ["Safety Vest"]),
        gloves=classes_raw.get("gloves", ["Gloves"]),
        goggles=classes_raw.get("goggles", ["Goggles"]),
        mask=classes_raw.get("mask", ["Mask"]),
        boots=classes_raw.get("boots", []),
        violation=classes_raw.get("violation", {}),
    )

    tracking = TrackingConfig(**data.get("tracking", {}))
    rules = RulesConfig(**data.get("rules", {}))

    display_raw = data.get("display", {})
    display = DisplayConfig(
        show_confidence=display_raw.get("show_confidence", True),
        alert_color=_to_tuple_color(display_raw.get("alert_color", [0, 0, 255])),
        person_color=_to_tuple_color(display_raw.get("person_color", [0, 255, 0])),
        ppe_color=_to_tuple_color(display_raw.get("ppe_color", [255, 200, 0])),
        window_name=display_raw.get("window_name", "PPE Detection"),
    )

    evidence = EvidenceConfig(**data.get("evidence", {}))
    storage = StorageConfig(**data.get("storage", {}))
    dashboard = DashboardConfig(**data.get("dashboard", {}))

    return AppConfig(
        camera=camera,
        model=model,
        classes=classes,
        tracking=tracking,
        rules=rules,
        display=display,
        evidence=evidence,
        storage=storage,
        dashboard=dashboard,
    )


def load_config(path: Path | str | None = None) -> AppConfig:
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    else:
        path = Path(path)

    if not path.exists():
        return AppConfig()

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return _build_config(data)


def load_cameras_config(path: Path | str | None = None) -> list[CameraEntry]:
    root = Path(__file__).resolve().parents[2]
    if path is None:
        path = root / "config" / "cameras.yaml"
    else:
        path = Path(path)
        if not path.is_absolute():
            path = root / path

    if not path.exists():
        return [CameraEntry(id="default", name="Câmera padrão", source="0")]

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cameras = data.get("cameras", [])
    return [CameraEntry(**c) for c in cameras]
