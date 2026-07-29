import datetime
from typing import Optional, List
from pydantic import BaseModel


class PersonBBox(BaseModel):
    track_id: int
    bbox: List[float]
    status: str  # "safe" | "smoking" | "violation"
    confidence: float


class CigaretteBBox(BaseModel):
    bbox: List[float]
    confidence: float


class FrameStats(BaseModel):
    total_persons: int
    smoking: int
    safe: int
    violations: int


class WebSocketPayload(BaseModel):
    timestamp: str
    camera_id: str
    persons: List[PersonBBox]
    cigarettes: List[CigaretteBBox]
    stats: FrameStats


class ViolationResponse(BaseModel):
    id: int
    camera_id: str
    track_id: int
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime] = None
    snapshot_path: Optional[str] = None
    confidence: Optional[float] = 0.0

    class Config:
        from_attributes = True


class CameraCreate(BaseModel):
    id: str
    name: str
    source_type: str = "webcam"
    source_url: str = "0"


class CameraResponse(BaseModel):
    id: str
    name: str
    source_type: str
    source_url: str
    status: str

    class Config:
        from_attributes = True


class StreamControlRequest(BaseModel):
    source: str = "0"
    camera_id: str = "cam-01"
