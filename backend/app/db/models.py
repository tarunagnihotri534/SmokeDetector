import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float
from backend.app.db.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(50), index=True, nullable=False, default="cam-01")
    track_id = Column(Integer, index=True, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    confidence = Column(Float, nullable=True, default=0.0)


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False, default="webcam") # "webcam", "file", "rtsp"
    source_url = Column(String(255), nullable=False, default="0")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
