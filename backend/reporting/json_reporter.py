import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def generate_json_report(detections: List[Dict[str, Any]], survey_info: Dict[str, Any], output_path: str) -> str:
    """
    Generate a JSON report matching API_SPEC.md.
    
    Args:
        detections: List of detection dictionaries.
        survey_info: Dictionary containing survey metadata.
        output_path: Path where the report should be saved.
        
    Returns:
        The output path.
    """
    report_data = {
        "survey_info": survey_info,
        "detections": detections,
        "summary": {
            "total_detections": len(detections),
            # In a real scenario, this would aggregate more details
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
        
    logger.info("JSON report generated at %s", output_path)
    return output_path
