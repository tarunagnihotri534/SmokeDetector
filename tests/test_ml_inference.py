import sys
from unittest.mock import MagicMock

# Mock cv2 if not present in environment
try:
    import cv2
except ImportError:
    mock_cv2 = MagicMock()
    mock_cv2.CAP_PROP_POS_FRAMES = 1
    sys.modules["cv2"] = mock_cv2

import pytest
import numpy as np
from ml.inference.config import OVERLAP_THRESH, DEBOUNCE_FRAMES
from ml.inference.containment import calculate_containment_ratio, match_persons_and_cigarettes
from ml.inference.stream_processor import StreamProcessor
from ml.inference.detector import DualYoloDetector


def test_containment_ratio_full_overlap():
    cig_box = [100, 100, 150, 150]
    person_box = [50, 50, 200, 200]
    ratio = calculate_containment_ratio(cig_box, person_box)
    assert ratio == 1.0


def test_containment_ratio_partial_overlap():
    cig_box = [180, 180, 220, 220]  # area = 40x40 = 1600
    person_box = [100, 100, 200, 200] # intersection [180, 180, 200, 200] = 20x20 = 400
    ratio = calculate_containment_ratio(cig_box, person_box)
    assert ratio == 400.0 / 1600.0  # 0.25


def test_containment_ratio_no_overlap():
    cig_box = [300, 300, 350, 350]
    person_box = [50, 50, 200, 200]
    ratio = calculate_containment_ratio(cig_box, person_box)
    assert ratio == 0.0


def test_match_persons_and_cigarettes():
    persons = [
        {"track_id": 1, "bbox": [50, 50, 200, 200]},
        {"track_id": 2, "bbox": [400, 400, 600, 600]}
    ]
    cigarettes = [
        {"bbox": [100, 100, 130, 130], "confidence": 0.8} # contained inside person 1
    ]
    smoking_ids = match_persons_and_cigarettes(persons, cigarettes, overlap_thresh=0.30)
    assert 1 in smoking_ids
    assert 2 not in smoking_ids


def test_stream_processor_debounce_state_machine():
    detector = DualYoloDetector()
    processor = StreamProcessor(detector=detector, debounce_frames=5)
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Process frame
    payload, _ = processor.process_single_frame(dummy_frame, frame_idx=1)
    assert "timestamp" in payload
    assert "camera_id" in payload
    assert "persons" in payload
    assert "cigarettes" in payload
    assert "stats" in payload
