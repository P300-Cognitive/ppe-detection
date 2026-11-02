"""Data models compartilhados por todos os módulos src/."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BBox = Tuple[int, int, int, int]  # x1, y1, x2, y2


@dataclass
class Detection:
    class_name: str
    confidence: float
    bbox: BBox
    track_id: Optional[int] = None
    person_id: Optional[int] = None


@dataclass
class TrackedPerson:
    track_id: int
    bbox: BBox


@dataclass
class Violation:
    person_id: int
    reason: str
    camera_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    bbox: Optional[BBox] = None


@dataclass
class Alert:
    person_id: int
    ppe_type: str
    camera_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Event:
    person_id: int
    camera_id: Optional[str]
    timestamp: datetime
    ppe_type: str


@dataclass
class Camera:
    id: str
    rtsp_url: str
    enabled: bool = True


@dataclass
class ConnectivityStatus:
    is_reachable: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None


@dataclass
class AIModel:
    id: str
    path: str
    is_active: bool = False


@dataclass
class NotificationResult:
    telegram_sent: bool = False
    email_sent: bool = False
    image_attached: bool = False


@dataclass
class Report:
    start: str
    end: str
    total_violations: int
    compliance_rate: float


@dataclass
class ImageMetadata:
    timestamp: datetime
    path: str


@dataclass
class VideoMetadata:
    pre_alert_seconds: int
    post_alert_seconds: int
    path: str


@dataclass
class DashboardView:
    active_streams: List[str]
    active_alerts: List[Alert] = field(default_factory=list)
