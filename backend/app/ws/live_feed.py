import asyncio
import cv2
import json
import logging
import datetime
from pathlib import Path
from typing import List, Set, Dict, Any, Optional, Tuple
from fastapi import WebSocket, WebSocketDisconnect

from backend.app.config import SNAPSHOTS_DIR
from backend.app.db.database import SessionLocal
from backend.app.db.models import Violation
from ml.inference.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket client connections and broadcasts frame JSON events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, payload: Dict[str, Any]):
        if not self.active_connections:
            return

        message = json.dumps(payload)
        to_remove = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error sending payload to client: {e}")
                to_remove.add(connection)

        for conn in to_remove:
            self.active_connections.discard(conn)


manager = ConnectionManager()

# Global stream processor and state tracker
active_stream_processor: Optional[StreamProcessor] = None
active_violations_db_map: Dict[Tuple[str, int], int] = {}  # (camera_id, track_id) -> violation_id


def save_violation_snapshot(camera_id: str, track_id: int, frame: Any) -> Optional[str]:
    """Saves a JPEG snapshot when a violation is confirmed."""
    try:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"violation_{camera_id}_id{track_id}_{timestamp_str}.jpg"
        filepath = SNAPSHOTS_DIR / filename

        if frame is not None and isinstance(frame, cv2.typing.MatLike if hasattr(cv2, 'typing') else object):
            cv2.imwrite(str(filepath), frame)
            return f"/snapshots/{filename}"
    except Exception as e:
        logger.error(f"Failed to save snapshot: {e}")
    return None


def handle_violation_event(payload: Dict[str, Any], snapshot_frame: Optional[Any] = None):
    """Processes violation start/end transitions and updates DB records."""
    camera_id = payload.get("camera_id", "cam-01")
    persons = payload.get("persons", [])

    db = SessionLocal()
    try:
        active_violation_tracks = set()

        for p in persons:
            t_id = p["track_id"]
            status = p["status"]
            conf = p.get("confidence", 0.0)

            if status == "violation":
                active_violation_tracks.add(t_id)
                key = (camera_id, t_id)

                # New violation record if not already active
                if key not in active_violations_db_map:
                    rel_path = None
                    if snapshot_frame is not None:
                        rel_path = save_violation_snapshot(camera_id, t_id, snapshot_frame)

                    new_violation = Violation(
                        camera_id=camera_id,
                        track_id=t_id,
                        started_at=datetime.datetime.now(datetime.timezone.utc),
                        snapshot_path=rel_path,
                        confidence=conf
                    )
                    db.add(new_violation)
                    db.commit()
                    db.refresh(new_violation)

                    active_violations_db_map[key] = new_violation.id
                    logger.info(f"Recorded new DB violation ID {new_violation.id} for track {t_id}")

        # Check for ended violations
        keys_to_remove = []
        for key, vio_id in active_violations_db_map.items():
            cam, t_id = key
            if cam == camera_id and t_id not in active_violation_tracks:
                # Mark ended_at timestamp in DB
                vio_rec = db.query(Violation).filter(Violation.id == vio_id).first()
                if vio_rec:
                    vio_rec.ended_at = datetime.datetime.now(datetime.timezone.utc)
                    db.commit()
                keys_to_remove.append(key)

        for k in keys_to_remove:
            active_violations_db_map.pop(k, None)

    except Exception as e:
        logger.error(f"DB Error handling violation event: {e}")
        db.rollback()
    finally:
        db.close()


async def websocket_live_feed_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive & handle any incoming messages from client
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)
