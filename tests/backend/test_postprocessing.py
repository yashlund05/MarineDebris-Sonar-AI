"""Unit and algorithmic tests for post-processing pipeline:

- True IoU calculation and global NMS suppression
- Acoustic shadow verification filtering
- Bounding box area constraint filtering
- Temperature scaling confidence calibration
"""

import pytest
from backend.inference.detector import RawDetection
from backend.postprocessing.nms import calculate_iou, apply_global_nms
from backend.postprocessing.size_filter import filter_by_size
from backend.postprocessing.shadow_filter import filter_shadow_artifacts
from backend.postprocessing.calibration import calibrate_confidence


def test_calculate_iou():
    """Verify IoU calculation for identical, overlapping, and disjoint boxes."""
    # Identical boxes
    box_a = (100, 100, 50, 50)
    box_b = (100, 100, 50, 50)
    assert calculate_iou(box_a, box_b) == 1.0

    # Disjoint boxes
    box_c = (200, 200, 50, 50)
    assert calculate_iou(box_a, box_c) == 0.0

    # Overlapping boxes (half-overlap along X)
    box_d = (125, 100, 50, 50)  # Overlap 25x50 = 1250, Union 2500+2500-1250 = 3750 => IoU = 1/3
    iou = calculate_iou(box_a, box_d)
    assert pytest.approx(iou, 0.01) == 1.0 / 3.0


def test_global_nms_suppression():
    """Verify that redundant overlapping detections of the same class are suppressed."""
    det1 = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.92,
        bbox_x=100,
        bbox_y=100,
        bbox_w=60,
        bbox_h=60,
        tile_row=0,
        tile_col=0,
    )
    # Heavily overlapping detection from an adjacent overlapping tile
    det2 = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.81,
        bbox_x=105,
        bbox_y=102,
        bbox_w=58,
        bbox_h=58,
        tile_row=0,
        tile_col=1,
    )
    # Distinct detection far away
    det3 = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.88,
        bbox_x=400,
        bbox_y=400,
        bbox_w=50,
        bbox_h=50,
        tile_row=1,
        tile_col=1,
    )

    survived = apply_global_nms([det1, det2, det3], iou_threshold=0.45)
    # det2 should be suppressed by det1; det3 should survive
    assert len(survived) == 2
    confidences = [d.confidence for d in survived]
    assert 0.92 in confidences
    assert 0.88 in confidences
    assert 0.81 not in confidences


def test_global_nms_different_classes_retained():
    """Verify that overlapping detections of DIFFERENT classes are NOT suppressed."""
    det_gear = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.90,
        bbox_x=100,
        bbox_y=100,
        bbox_w=50,
        bbox_h=50,
        tile_row=0,
        tile_col=0,
    )
    det_pipe = RawDetection(
        class_id=3,
        class_name="pipe_or_cylinder",
        confidence=0.85,
        bbox_x=100,
        bbox_y=100,
        bbox_w=50,
        bbox_h=50,
        tile_row=0,
        tile_col=0,
    )

    survived = apply_global_nms([det_gear, det_pipe], iou_threshold=0.45)
    assert len(survived) == 2


def test_filter_by_size():
    """Verify bounding box area filtering."""
    tiny = RawDetection(
        class_id=1,
        class_name="general_marine_debris",
        confidence=0.7,
        bbox_x=0,
        bbox_y=0,
        bbox_w=5,
        bbox_h=5,
        tile_row=0,
        tile_col=0,
    )  # area = 25
    valid = RawDetection(
        class_id=1,
        class_name="general_marine_debris",
        confidence=0.7,
        bbox_x=0,
        bbox_y=0,
        bbox_w=50,
        bbox_h=50,
        tile_row=0,
        tile_col=0,
    )  # area = 2500

    results = filter_by_size([tiny, valid], min_area_px=100, max_area_px=50000)
    assert tiny.is_filtered is True
    assert tiny.filtered_reason == "size_constraint"
    assert valid.is_filtered is False


def test_calibrate_confidence():
    """Verify temperature scaling calibration preserves ranking while adjusting probabilities."""
    det_high = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.90,
        bbox_x=0,
        bbox_y=0,
        bbox_w=10,
        bbox_h=10,
        tile_row=0,
        tile_col=0,
    )
    det_low = RawDetection(
        class_id=0,
        class_name="derelict_fishing_gear",
        confidence=0.60,
        bbox_x=0,
        bbox_y=0,
        bbox_w=10,
        bbox_h=10,
        tile_row=0,
        tile_col=0,
    )

    calibrated = calibrate_confidence([det_high, det_low], temperature=1.4)
    # Raw confidence must be unchanged
    assert det_high.confidence == 0.90
    assert det_low.confidence == 0.60
    # Calibrated confidence must be set
    assert det_high.confidence_calibrated is not None
    assert det_low.confidence_calibrated is not None
    # Temperature > 1 softens extreme confidences (0.90 becomes slightly lower)
    assert det_high.confidence_calibrated < 0.90
    # Relative ordering must be strictly preserved
    assert det_high.confidence_calibrated > det_low.confidence_calibrated
