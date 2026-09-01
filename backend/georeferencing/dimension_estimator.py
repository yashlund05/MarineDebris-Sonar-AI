from typing import Optional, Dict, Any

def estimate_dimensions(
    bbox_w: int, bbox_h: int,
    range_resolution_m: Optional[float] = None,
    along_track_resolution_m: Optional[float] = None,
) -> dict[str, Optional[float]]:
    """
    Estimate the physical dimensions of a detected object based on its bounding box
    and the sonar resolution.
    
    Args:
        bbox_w: Width of the bounding box in pixels.
        bbox_h: Height of the bounding box in pixels.
        range_resolution_m: Meters per pixel in across-track.
        along_track_resolution_m: Meters per pixel in along-track.
        
    Returns:
        Dict containing estimated_length_m and estimated_width_m.
    """
    estimated_length_m = None
    estimated_width_m = None
    
    if along_track_resolution_m is not None:
        estimated_length_m = float(bbox_h * along_track_resolution_m)
        
    if range_resolution_m is not None:
        estimated_width_m = float(bbox_w * range_resolution_m)
        
    return {
        "estimated_length_m": estimated_length_m,
        "estimated_width_m": estimated_width_m
    }
