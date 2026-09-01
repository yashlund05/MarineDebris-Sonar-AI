"""End-to-end ML inference pipeline executing detection, segmentation, and classification."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

from backend.ml.detector.yolo_detector import YOLOv8Detector
from backend.ml.segmentation.unet import UNetSegmenter
from backend.ml.classifier.mobilenet import MobileNetClassifier
from backend.ml.fusion.inference_fusion import InferenceFusion
from backend.postprocessing.nms import apply_global_nms
from backend.postprocessing.size_filter import filter_by_size
from backend.postprocessing.shadow_filter import filter_shadow_artifacts
from backend.postprocessing.calibration import calibrate_confidence
from backend.georeferencing.dimension_estimator import estimate_dimensions
from backend.georeferencing.geotagger import geotag_detection

logger = logging.getLogger(__name__)


class InferencePipeline:
    """Orchestrates multi-stage ML inference over acoustic sonar tiles."""

    def __init__(
        self,
        detector: Optional[YOLOv8Detector] = None,
        segmenter: Optional[UNetSegmenter] = None,
        classifier: Optional[MobileNetClassifier] = None,
    ):
        self.detector = detector or YOLOv8Detector()
        self.segmenter = segmenter or UNetSegmenter()
        self.classifier = classifier or MobileNetClassifier()

    def process_tiles(
        self,
        tiles: List[Any],
        tile_infos: List[Any],
        conf_threshold: float = 0.35,
        nms_iou_threshold: float = 0.45,
        enable_segmentation: bool = True,
        enable_classification: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute full detection pipeline on acoustic tiles."""
        # 1. Detection
        raw_tile_dets = self.detector.predict(tiles, conf_threshold=conf_threshold)

        # Flatten detections
        flat_dets = []
        for det_list in raw_tile_dets:
            flat_dets.extend(det_list)

        if not flat_dets:
            logger.info("No raw detections found across acoustic tiles.")
            return []

        # 2. Global NMS & coordinate adjustment
        post_nms = apply_global_nms(flat_dets, tile_infos, iou_threshold=nms_iou_threshold)

        # 3. Acoustic Filtering
        filtered = filter_by_size(post_nms)
        filtered = filter_shadow_artifacts(filtered)
        filtered = calibrate_confidence(filtered)

        results = []
        for det in filtered:
            # Prepare bounding box dictionary
            bbox = {
                "x": det.bbox_x,
                "y": det.bbox_y,
                "width": det.bbox_w,
                "height": det.bbox_h,
            }

            # 4. Segmentation (graceful degradation if unavailable)
            seg_res = None
            if enable_segmentation:
                seg_res = self.segmenter.predict(tile=None, bbox=bbox)
            seg_dict = {
                "status": seg_res.status if seg_res else "unavailable",
                "confidence": seg_res.confidence if seg_res else None,
                "mask_area": seg_res.mask_area if seg_res else None,
                "mask_rle": seg_res.mask_rle if seg_res else None,
            }

            # 5. Secondary Classification (optional)
            classif_res = None
            if enable_classification:
                classif_res = self.classifier.predict(crop=np.array([]))
            fused = InferenceFusion.fuse(
                detector_class=det.class_name,
                detector_confidence=det.confidence,
                classification_result=classif_res or self.classifier.predict(np.array([])),
                classifier_name=self.classifier.model_name if enable_classification else None,
            )

            # 6. Physical Dimensions
            dims = estimate_dimensions(bbox_w=det.bbox_w, bbox_h=det.bbox_h)

            det_entry = {
                "class_id": det.class_id,
                "class_name": fused.final_class_name,
                "confidence": det.confidence,
                "confidence_calibrated": det.confidence_calibrated,
                "bbox": bbox,
                "segmentation": seg_dict,
                "classification": {
                    "status": fused.classification_status,
                    "model": fused.classifier_model,
                    "class_name": fused.classifier_class,
                    "confidence": fused.classifier_confidence,
                    "agreement": fused.classification_agreement,
                },
                "dimensions": dims,
                "is_filtered": det.is_filtered,
                "filtered_reason": det.filtered_reason,
            }
            results.append(det_entry)

        return results
