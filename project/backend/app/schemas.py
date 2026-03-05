from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ThreatEvent(BaseModel):
    person_id: int
    threat_score: int = Field(ge=0, le=100)
    type: str
    timestamp: datetime
    source_video: Optional[str] = None
    scene: Optional[str] = None
    bbox: Optional[List[float]] = None
    frame_idx: Optional[int] = None


class ThreatResponse(BaseModel):
    status: str
    message: str
    events: List[ThreatEvent] = []


class AnalysisResult(BaseModel):
    status: str
    message: str
    total_frames: int = 0
    persons_detected: int = 0
    alerts: int = 0
    events: List[ThreatEvent] = []
    max_threat_score: int = 0
    scene: str = "aggression"
