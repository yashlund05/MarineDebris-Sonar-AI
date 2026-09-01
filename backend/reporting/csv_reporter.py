import csv
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def generate_csv_report(detections: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate a CSV report of detections.
    
    Args:
        detections: List of detection dictionaries.
        output_path: Path where the report should be saved.
        
    Returns:
        The output path.
    """
    fieldnames = [
        "detection_id",
        "detection_code",
        "class_name",
        "confidence",
        "confidence_calibrated",
        "bbox_x",
        "bbox_y",
        "bbox_w",
        "bbox_h",
        "estimated_length_m",
        "estimated_width_m",
        "geotagging_available",
        "latitude",
        "longitude",
        "ping_number",
        "ping_timestamp",
        "is_filtered",
        "filtered_reason"
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for det in detections:
            row = {}
            for field in fieldnames:
                # Map id -> detection_id if not present
                if field == "detection_id" and "id" in det and "detection_id" not in det:
                    row[field] = str(det["id"])
                else:
                    row[field] = det.get(field)
            writer.writerow(row)
            
    logger.info("CSV report generated at %s", output_path)
    return output_path
