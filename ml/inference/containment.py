from typing import List, Tuple, Dict, Any, Set
from .config import OVERLAP_THRESH


def calculate_containment_ratio(cig_box: List[float], person_box: List[float]) -> float:
    """
    Computes what fraction of the cigarette's bounding box area lies inside the person's bounding box.
    
    bbox format: [x1, y1, x2, y2]
    
    Returns:
        float: Containment ratio between 0.0 and 1.0.
    """
    cx1, cy1, cx2, cy2 = cig_box
    px1, py1, px2, py2 = person_box

    cig_w = max(0.0, cx2 - cx1)
    cig_h = max(0.0, cy2 - cy1)
    cig_area = cig_w * cig_h

    if cig_area <= 0.0:
        return 0.0

    # Intersection rectangle
    ix1 = max(cx1, px1)
    iy1 = max(cy1, py1)
    ix2 = min(cx2, px2)
    iy2 = min(cy2, py2)

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    inter_area = inter_w * inter_h

    return inter_area / cig_area


def check_person_containment(
    person_bbox: List[float],
    cig_bboxes: List[List[float]],
    overlap_thresh: float = OVERLAP_THRESH
) -> Tuple[bool, float]:
    """
    Checks if any cigarette bbox is sufficiently contained within a given person's bbox.
    
    Returns:
        Tuple[bool, float]: (is_smoking, max_containment_ratio_found)
    """
    max_ratio = 0.0
    for cig_box in cig_bboxes:
        ratio = calculate_containment_ratio(cig_box, person_bbox)
        if ratio > max_ratio:
            max_ratio = ratio
        if max_ratio >= overlap_thresh:
            return True, max_ratio
            
    return max_ratio >= overlap_thresh, max_ratio


def match_persons_and_cigarettes(
    persons: List[Dict[str, Any]],
    cigarettes: List[Dict[str, Any]],
    overlap_thresh: float = OVERLAP_THRESH
) -> Set[int]:
    """
    Matches cigarettes to persons based on containment ratio threshold.
    
    Args:
        persons: List of dicts, each containing 'track_id' (or index) and 'bbox'
        cigarettes: List of dicts, each containing 'bbox' and 'confidence'
        overlap_thresh: Containment ratio threshold (default from config)
        
    Returns:
        Set of track_ids (or person indices) that are linked to at least one cigarette.
    """
    smoking_person_ids: Set[int] = set()

    for cig in cigarettes:
        cig_box = cig["bbox"]
        best_person_id = None
        best_ratio = 0.0

        for person in persons:
            p_box = person["bbox"]
            ratio = calculate_containment_ratio(cig_box, p_box)
            if ratio >= overlap_thresh and ratio > best_ratio:
                best_ratio = ratio
                best_person_id = person.get("track_id")

        if best_person_id is not None:
            smoking_person_ids.add(best_person_id)

    return smoking_person_ids
