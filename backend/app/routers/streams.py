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
        self.current_source: str = "6570562-hd_1080_1920_25fps.mp4"
        self.current_camera_id: str = "cam-01"
        self.latest_jpeg_frame: Optional[bytes] = None

    def start_stream(self, source: str = "6570562-hd_1080_1920_25fps.mp4", camera_id: str = "cam-01"):
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
    """Generates live MJPEG frames from the stream processor for browser video display."""
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

        # If live processor is active and has an annotated frame, stream it
        if stream_manager.processor and stream_manager.processor.latest_annotated_frame is not None:
            frame_to_send = stream_manager.processor.latest_annotated_frame
            _, encoded = cv2.imencode(".jpg", frame_to_send)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + encoded.tobytes() + b'\r\n')
            await asyncio.sleep(1.0 / 15.0)
            continue

        # Fallback synthetic frame while initializing
        frame_idx += 1
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.rectangle(img, (0, 0), (1280, 720), (30, 30, 40), -1)
        cv2.putText(img, f"INITIALIZING FEED ({stream_manager.current_camera_id})...", (40, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
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
