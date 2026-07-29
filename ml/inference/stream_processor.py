import asyncio
import cv2
import datetime
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional, Callable, List, Tuple
import numpy as np

from .config import DEBOUNCE_FRAMES, OVERLAP_THRESH
from .containment import match_persons_and_cigarettes
from .detector import DualYoloDetector

logger = logging.getLogger(__name__)


class StreamProcessor:
    """
    Processes video stream frames, executes dual YOLO detection & containment linking,
    tracks per-person debounce state, and yields JSON events matching the WebSocket contract.
    """

    def __init__(
        self,
        detector: Optional[DualYoloDetector] = None,
        debounce_frames: int = DEBOUNCE_FRAMES,
        camera_id: str = "cam-01",
        on_violation_cb: Optional[Callable[[Dict[str, Any], np.ndarray], None]] = None
    ):
        self.detector = detector if detector is not None else DualYoloDetector()
        self.debounce_frames = debounce_frames
        self.camera_id = camera_id
        self.on_violation_cb = on_violation_cb
        
        # Debounce state machine: track_id -> consecutive_smoking_count
        self.track_smoking_counts: Dict[int, int] = {}
        # Track previous status per track_id to detect transitions
        self.previous_statuses: Dict[int, str] = {}

    def reset_state(self):
        self.track_smoking_counts.clear()
        self.previous_statuses.clear()

    def process_single_frame(
        self,
        frame: np.ndarray,
        frame_idx: int = 0
    ) -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
        """
        Process a single image frame (numpy BGR array) and return structured payload.
        """
        # Run dual YOLO detector
        persons_raw, cigarettes_raw = self.detector.process_frame(frame, frame_idx)

        # Match cigarettes to persons based on containment ratio
        smoking_track_ids = match_persons_and_cigarettes(
            persons=persons_raw,
            cigarettes=cigarettes_raw,
            overlap_thresh=OVERLAP_THRESH
        )

        processed_persons = []
        active_track_ids = set()
        
        total_persons = len(persons_raw)
        smoking_count = 0
        safe_count = 0
        violations_count = 0

        snapshot_frame = None

        for p in persons_raw:
            t_id = p["track_id"]
            active_track_ids.add(t_id)

            is_smoking_this_frame = t_id in smoking_track_ids

            if is_smoking_this_frame:
                self.track_smoking_counts[t_id] = self.track_smoking_counts.get(t_id, 0) + 1
            else:
                # Reset counter if not smoking in current frame
                self.track_smoking_counts[t_id] = 0

            consecutive = self.track_smoking_counts[t_id]

            # Determine state: safe | smoking | violation
            if consecutive >= self.debounce_frames:
                status = "violation"
                violations_count += 1
            elif is_smoking_this_frame:
                status = "smoking"
                smoking_count += 1
            else:
                status = "safe"
                safe_count += 1

            prev_status = self.previous_statuses.get(t_id, "safe")
            
            # Check transition to violation
            if status == "violation" and prev_status != "violation":
                logger.info(f"[CAMERA {self.camera_id}] Track ID {t_id} entered VIOLATION state!")
                snapshot_frame = frame.copy()

            self.previous_statuses[t_id] = status

            processed_persons.append({
                "track_id": t_id,
                "bbox": p["bbox"],
                "status": status,
                "confidence": p["confidence"]
            })

        # Cleanup tracks no longer visible
        stale_tracks = set(self.track_smoking_counts.keys()) - active_track_ids
        for st in stale_tracks:
            self.track_smoking_counts.pop(st, None)
            self.previous_statuses.pop(st, None)

        payload = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "camera_id": self.camera_id,
            "persons": processed_persons,
            "cigarettes": cigarettes_raw,
            "stats": {
                "total_persons": total_persons,
                "smoking": smoking_count,
                "safe": safe_count,
                "violations": violations_count
            }
        }

        if snapshot_frame is not None and self.on_violation_cb is not None:
            self.on_violation_cb(payload, snapshot_frame)

        return payload, snapshot_frame

    async def stream_source(
        self,
        source: Any = 0,
        fps_target: float = 15.0
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator yielding frame payloads for video source (file path, webcam int, or RTSP URL).
        """
        cap = None
        is_numeric = isinstance(source, int) or (isinstance(source, str) and source.isdigit())
        source_val = int(source) if is_numeric else source

        try:
            cap = cv2.VideoCapture(source_val)
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {source}")
                # Yield synthetic frame stream if source cannot be opened
                async for mock_payload in self._mock_stream_generator(fps_target):
                    yield mock_payload
                return

            frame_idx = 0
            frame_delay = 1.0 / fps_target

            while True:
                ret, frame = cap.read()
                if not ret:
                    if not is_numeric:
                        # Loop video file for continuous demonstration
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        break

                frame_idx += 1
                payload, _ = self.process_single_frame(frame, frame_idx)
                yield payload

                await asyncio.sleep(frame_delay)

        finally:
            if cap is not None and cap.isOpened():
                cap.release()

    async def _mock_stream_generator(self, fps_target: float = 15.0) -> AsyncGenerator[Dict[str, Any], None]:
        """Fallback mock frame stream when physical video capture is unavailable."""
        frame_idx = 0
        frame_delay = 1.0 / fps_target
        dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        while True:
            frame_idx += 1
            payload, _ = self.process_single_frame(dummy_frame, frame_idx)
            yield payload
            await asyncio.sleep(frame_delay)
