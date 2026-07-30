import asyncio
import cv2
import datetime
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional, Callable, List, Tuple
import numpy as np

from .config import DEBOUNCE_FRAMES, OVERLAP_THRESH, BASE_DIR
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
        # Latest annotated frame image for live MJPEG HTTP streaming
        self.latest_annotated_frame: Optional[np.ndarray] = None

    def reset_state(self):
        self.track_smoking_counts.clear()
        self.previous_statuses.clear()
        self.latest_annotated_frame = None

    def draw_annotations(self, frame: np.ndarray, persons: List[Dict[str, Any]], cigarettes: List[Dict[str, Any]]) -> np.ndarray:
        """Render detection bounding boxes and labels onto a frame copy."""
        annotated = frame.copy()
        
        # 1. Draw cigarettes (Orange)
        for cig in cigarettes:
            bbox = cig.get("bbox", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = [int(c) for c in bbox]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (249, 115, 22), 2)
                conf = cig.get("confidence", 0.0)
                label = f"cigarette {conf:.2f}"
                cv2.putText(annotated, label, (x1, max(15, y1 - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (249, 115, 22), 1)

        # 2. Draw persons (Green = Safe, Orange = Smoking, Red = Violation)
        for p in persons:
            bbox = p.get("bbox", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = [int(c) for c in bbox]
                status = p.get("status", "safe")
                track_id = p.get("track_id", 0)
                conf = p.get("confidence", 0.0)

                if status == "violation":
                    color = (239, 68, 68)     # Red
                    tag = " [VIOLATION]"
                elif status == "smoking":
                    color = (249, 115, 22)    # Orange
                    tag = " [SMOKING]"
                else:
                    color = (34, 197, 94)     # Green
                    tag = ""

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} person {conf:.2f}{tag}"
                cv2.putText(annotated, label, (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return annotated

    def process_single_frame(
        self,
        frame: np.ndarray,
        frame_idx: int = 0
    ) -> Tuple[Dict[str, Any], Optional[np.ndarray]]:
        """
        Process a single image frame (numpy BGR array) and return structured payload.
        """
        h, w = frame.shape[:2] if hasattr(frame, 'shape') else (720, 1280)

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
            "frame_width": w,
            "frame_height": h,
            "persons": processed_persons,
            "cigarettes": cigarettes_raw,
            "stats": {
                "total_persons": total_persons,
                "smoking": smoking_count,
                "safe": safe_count,
                "violations": violations_count
            }
        }

        # Store annotated frame for live feed MJPEG output
        self.latest_annotated_frame = self.draw_annotations(frame, processed_persons, cigarettes_raw)

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

        if not is_numeric:
            p = Path(str(source))
            if not p.is_file():
                candidates = [
                    BASE_DIR / "backend" / "app" / str(source),
                    BASE_DIR / "backend" / "app" / p.name,
                    BASE_DIR / str(source),
                    BASE_DIR / p.name
                ]
                for cand in candidates:
                    if cand.is_file():
                        source_val = str(cand)
                        logger.info(f"Resolved video file path to: {source_val}")
                        break

        try:
            cap = cv2.VideoCapture(source_val)
            if not cap.isOpened():
                logger.error(f"Failed to open video source: {source_val}")
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

