import logging
from typing import List, Dict, Tuple, Optional
from backend.inference.detector import RawDetection

logger = logging.getLogger(__name__)


def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """Calculate Intersection over Union (IoU) of two bounding boxes (x, y, w, h)."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)

    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter_area = inter_w * inter_h

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / float(union_area)


def apply_global_nms(
    all_detections: List[RawDetection],
    tile_infos: Optional[list] = None,
    iou_threshold: float = 0.45,
) -> List[RawDetection]:
    """
    Apply Non-Maximum Suppression (NMS) across all tiles to remove duplicate detections 
    from overlapping tile regions.
    """
    if not all_detections:
        return []

    logger.info(
        "Applying global NMS on %d detections with iou_threshold=%.2f",
        len(all_detections),
        iou_threshold,
    )

    # Group detections by class so suppression is class-specific
    by_class: Dict[int, List[RawDetection]] = {}
    for det in all_detections:
        by_class.setdefault(det.class_id, []).append(det)

    survived_detections: List[RawDetection] = []

    for class_id, dets in by_class.items():
        # Sort by confidence descending
        sorted_dets = sorted(dets, key=lambda d: d.confidence, reverse=True)
        keep: List[RawDetection] = []

        while sorted_dets:
            current = sorted_dets.pop(0)
            keep.append(current)

            curr_box = (current.bbox_x, current.bbox_y, current.bbox_w, current.bbox_h)
            remaining: List[RawDetection] = []
            for candidate in sorted_dets:
                cand_box = (candidate.bbox_x, candidate.bbox_y, candidate.bbox_w, candidate.bbox_h)
                iou = calculate_iou(curr_box, cand_box)
                if iou < iou_threshold:
                    remaining.append(candidate)
            sorted_dets = remaining

        survived_detections.extend(keep)

    logger.info("Global NMS: %d detections survived from %d input", len(survived_detections), len(all_detections))
    return survived_detections
