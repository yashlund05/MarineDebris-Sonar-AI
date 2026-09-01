import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def generate_geojson_report(detections: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate a GeoJSON report of geotagged detections.
    
    Args:
        detections: List of detection dictionaries.
        output_path: Path where the report should be saved.
        
    Returns:
        The output path.
    """
    features = []
    
    for det in detections:
        if not det.get("geotagging_available", False):
            continue
            
        lat = det.get("latitude")
        lon = det.get("longitude")
        
        if lat is None or lon is None:
            continue
            
        # Serialize UUIDs if present to avoid JSON encoding errors
        properties = {}
        for k, v in det.items():
            properties[k] = str(v) if hasattr(v, 'hex') else v
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]  # GeoJSON format is [longitude, latitude]
            },
            "properties": properties
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
        
    logger.info("GeoJSON report generated at %s", output_path)
    return output_path
