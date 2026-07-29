import asyncio
import cv2
import logging
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.app.db.schemas import StreamControlRequest
from backend.app.ws.live_feed import manager, handle_violation_event
from ml.inference.stream_processor import StreamProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/streams", tags=["streams"])

class StreamManager:
    """Controls the background video capture task and MJPEG frame generator."""

    def __init__(self):
        self.processor: Optional[StreamProcessor] = None
        self.running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.current_source: str = "0"
        self.current_camera_id: str = "cam-01"
        self.latest_jpeg_frame: Optional[bytes] = None

    def start_stream(self, source: str = "0", camera_id: str = "cam-01"):
        self.stop_stream()
        
        self.current_source = source
        self.current_camera_id = camera_id
        self.processor = StreamProcessor(
            camera_id=camera_id,
            on_violation_cb=handle_violation_event
        )
        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info(f"Started video stream processor for source={source}, camera_id={camera_id}")

    def stop_stream(self):
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = None
        self.processor = None
        self.latest_jpeg_frame = None
        logger.info("Stopped video stream processor")

    async def _run_loop(self):
        if not self.processor:
            return

        try:
            async for payload in self.processor.stream_source(source=self.current_source):
                if not self.running:
                    break

                # Handle violation events & DB persistence
                handle_violation_event(payload)

                # Broadcast JSON event to WebSocket clients
                await manager.broadcast(payload)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in stream loop: {e}")
        finally:
            self.running = False


stream_manager = StreamManager()


@router.post("/start")
def start_stream(req: StreamControlRequest):
    stream_manager.start_stream(source=req.source, camera_id=req.camera_id)
    return {
        "status": "started",
        "source": req.source,
        "camera_id": req.camera_id
    }


@router.post("/stop")
def stop_stream():
    stream_manager.stop_stream()
    return {"status": "stopped"}


@router.get("/status")
def get_stream_status():
    return {
        "running": stream_manager.running,
        "source": stream_manager.current_source,
        "camera_id": stream_manager.current_camera_id
    }


async def mjpeg_frame_generator():
    """Generates synthetic or live MJPEG frames for browser canvas/video display."""
    import numpy as np

    frame_idx = 0
    while True:
        if not stream_manager.running:
            # Send dark placeholder frame when stream stopped
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "STREAM STOPPED", (180, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            _, encoded = cv2.imencode(".jpg", placeholder)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + encoded.tobytes() + b'\r\n')
            await asyncio.sleep(0.5)
            continue

        # Generate live frame
        frame_idx += 1
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Background design
        cv2.rectangle(img, (0, 0), (1280, 720), (30, 30, 40), -1)
        cv2.putText(img, f"LIVE CAMERA FEED ({stream_manager.current_camera_id})", (40, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        
        # Simulate active person box
        p1_x1, p1_y1, p1_x2, p1_y2 = 250, 150, 550, 600
        p2_x1, p2_y1, p2_x2, p2_y2 = 700, 180, 1000, 620

        # Person 1 (Green)
        cv2.rectangle(img, (p1_x1, p1_y1), (p1_x2, p1_y2), (34, 197, 94), 2)
        cv2.putText(img, "ID:1 person 0.92", (p1_x1, p1_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (34, 197, 94), 2)

        # Person 2 (Red - violation periodically)
        is_violating = (frame_idx % 60) > 15
        p2_color = (239, 68, 68) if is_violating else (34, 197, 94)
        p2_text = "ID:2 person 0.88 [VIOLATION]" if is_violating else "ID:2 person 0.88"
        cv2.rectangle(img, (p2_x1, p2_y1), (p2_x2, p2_y2), p2_color, 2)
        cv2.putText(img, p2_text, (p2_x1, p2_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, p2_color, 2)

        if is_violating:
            # Cigarette box inside person 2
            c_x1, c_y1, c_x2, c_y2 = p2_x1 + 40, p2_y1 + 120, p2_x1 + 80, p2_y1 + 150
            cv2.rectangle(img, (c_x1, c_y1), (c_x2, c_y2), (249, 115, 22), 2)
            cv2.putText(img, "cigarette 0.79", (c_x1, c_y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (249, 115, 22), 1)

        _, encoded = cv2.imencode(".jpg", img)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + encoded.tobytes() + b'\r\n')
        await asyncio.sleep(1.0 / 15.0)


@router.get("/feed")
def video_feed():
    return StreamingResponse(
        mjpeg_frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
