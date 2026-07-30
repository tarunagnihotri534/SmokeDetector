import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from .config import (
    PERSON_CONF,
    CIG_CONF,
    IOU_THRESH,
    PERSON_MODEL,
    CIGARETTE_MODEL,
)

logger = logging.getLogger(__name__)


class DualYoloDetector:
    """
    Dual YOLO detector for Cigarette Violation Detection.
    - Person detector: YOLOv11s (class 0) with ByteTrack for persistent ID tracking.
    - Cigarette detector: Custom YOLOv11s (best.pt) for cigarette detection.
    """

    def __init__(
        self,
        person_model_path: str = PERSON_MODEL,
        cigarette_model_path: str = CIGARETTE_MODEL,
        person_conf: float = PERSON_CONF,
        cig_conf: float = CIG_CONF,
        iou_thresh: float = IOU_THRESH,
    ):
        self.person_conf = person_conf
        self.cig_conf = cig_conf
        self.iou_thresh = iou_thresh
        
        self.person_model = None
        self.cigarette_model = None
        self.using_mock_cig = False
        self.use_predict_fallback = False

        self._load_models(person_model_path, cigarette_model_path)

    def _load_models(self, person_path: str, cig_path: str):
        try:
            from ultralytics import YOLO
            
            # Load Person model (yolo11s.pt will auto-download if missing)
            logger.info(f"Loading person tracking model: {person_path}")
            self.person_model = YOLO(person_path)

            # Load Cigarette model if present
            cig_file = Path(cig_path)
            if cig_file.exists() and cig_file.stat().st_size > 0:
                logger.info(f"Loading custom cigarette detection model: {cig_path}")
                self.cigarette_model = YOLO(cig_path)
            else:
                logger.warning(
                    f"Cigarette model file '{cig_path}' not found. "
                    "Running in fallback mode (person tracking active; cigarette detection simulated or mock)."
                )
                self.using_mock_cig = True
        except ImportError:
            logger.warning("Ultralytics library not installed. Running detector in synthetic mock mode.")
            self.person_model = None
            self.cigarette_model = None
            self.using_mock_cig = True

    def process_frame(
        self, frame: np.ndarray, frame_idx: int = 0
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes a single frame image (BGR numpy array).
        
        Returns:
            Tuple[persons, cigarettes]:
                persons: List of dicts [{"track_id": int, "bbox": [x1,y1,x2,y2], "confidence": float}]
                cigarettes: List of dicts [{"bbox": [x1,y1,x2,y2], "confidence": float}]
        """
        persons = []
        cigarettes = []

        if self.person_model is not None:
            # 1. Run Person Tracking (class 0 = person)
            if self.use_predict_fallback:
                track_results = self.person_model.predict(
                    source=frame,
                    classes=[0],
                    conf=self.person_conf,
                    iou=self.iou_thresh,
                    verbose=False
                )
            else:
                try:
                    track_results = self.person_model.track(
                        source=frame,
                        persist=True,
                        tracker="bytetrack.yaml",
                        classes=[0],
                        conf=self.person_conf,
                        iou=self.iou_thresh,
                        verbose=False
                    )
                except Exception as e:
                    logger.warning(f"ByteTrack tracking failed ({e}); falling back to predict()")
                    self.use_predict_fallback = True
                    track_results = self.person_model.predict(
                        source=frame,
                        classes=[0],
                        conf=self.person_conf,
                        iou=self.iou_thresh,
                        verbose=False
                    )

            if track_results and len(track_results) > 0 and track_results[0].boxes is not None:
                boxes = track_results[0].boxes
                for i, box in enumerate(boxes):
                    cls_id = int(box.cls[0].item()) if box.cls is not None else 0
                    if cls_id != 0:
                        continue
                    
                    bbox = box.xyxy[0].cpu().numpy().tolist()
                    conf = float(box.conf[0].item()) if box.conf is not None else 0.0
                    track_id = int(box.id[0].item()) if (box.id is not None and len(box.id) > 0) else (i + 1)
                    
                    persons.append({
                        "track_id": track_id,
                        "bbox": [round(c, 2) for c in bbox],
                        "confidence": round(conf, 4)
                    })

            # 2. Run Cigarette Detection
            if self.cigarette_model is not None and not self.using_mock_cig:
                cig_results = self.cigarette_model.predict(
                    source=frame,
                    conf=self.cig_conf,
                    iou=self.iou_thresh,
                    verbose=False
                )
                if cig_results and len(cig_results) > 0 and cig_results[0].boxes is not None:
                    c_boxes = cig_results[0].boxes
                    for c_box in c_boxes:
                        bbox = c_box.xyxy[0].cpu().numpy().tolist()
                        conf = float(c_box.conf[0].item()) if c_box.conf is not None else 0.0
                        cigarettes.append({
                            "bbox": [round(c, 2) for c in bbox],
                            "confidence": round(conf, 4)
                        })

        # Fallback/mock generator if no real model or running demo synthetic frames
        if self.person_model is None or (len(persons) == 0 and frame_idx > 0 and self.using_mock_cig):
            persons, cigarettes = self._generate_mock_detections(frame, frame_idx)

        return persons, cigarettes

    def _generate_mock_detections(
        self, frame: np.ndarray, frame_idx: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Synthetic detection generator for testing UI & WebSocket when models are absent or video is dummy."""
        h, w = frame.shape[:2] if hasattr(frame, 'shape') else (720, 1280)
        
        # Simulating 2 persons
        p1_x1 = int(w * 0.2)
        p1_y1 = int(h * 0.2)
        p1_x2 = int(w * 0.45)
        p1_y2 = int(h * 0.8)

        p2_x1 = int(w * 0.55)
        p2_y1 = int(h * 0.25)
        p2_x2 = int(w * 0.85)
        p2_y2 = int(h * 0.85)

        persons = [
            {"track_id": 1, "bbox": [p1_x1, p1_y1, p1_x2, p1_y2], "confidence": 0.92},
            {"track_id": 2, "bbox": [p2_x1, p2_y1, p2_x2, p2_y2], "confidence": 0.88},
        ]

        cigarettes = []
        # Periodically simulate a cigarette inside person 1's bbox to test violation state transition
        if (frame_idx % 60) > 15:
            # Cigarette bbox inside person 1
            cig_x1 = p1_x1 + 30
            cig_y1 = p1_y1 + 100
            cig_x2 = cig_x1 + 40
            cig_y2 = cig_y1 + 30
            cigarettes.append({
                "bbox": [cig_x1, cig_y1, cig_x2, cig_y2],
                "confidence": 0.79
            })

        return persons, cigarettes
