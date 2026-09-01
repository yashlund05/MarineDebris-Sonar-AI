import math
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# WGS84 Earth radius in metres
EARTH_RADIUS_M = 6_371_000.0

def geotag_detection(
    bbox_x: int, bbox_y: int, bbox_w: int, bbox_h: int,
    ping_latitude: Optional[float], ping_longitude: Optional[float],
    ping_heading: Optional[float], ping_altitude: Optional[float],
    range_resolution_m: Optional[float],
    channel: str = 'starboard',
    image_width: int = 1024,
) -> dict:
    """
    Project a detection from pixel coordinates to WGS84 geographical coordinates.
    
    Args:
        bbox_x, bbox_y, bbox_w, bbox_h: Bounding box of the detection in pixels.
        ping_latitude, ping_longitude: Position of the towfish at this ping.
        ping_heading: Heading of the towfish in degrees.
        ping_altitude: Altitude of the towfish (distance from bottom) in meters.
        range_resolution_m: Meters per pixel in the across-track direction.
        channel: 'port' or 'starboard' (determines projection side).
        image_width: Width of the channel image in pixels.
        
    Returns:
        Dict with geotagging_available, latitude, and longitude.
    """
    if ping_latitude is None or ping_longitude is None or ping_heading is None:
        logger.debug("Missing navigation data, cannot geotag detection.")
        return {
            "geotagging_available": False,
            "latitude": None,
            "longitude": None
        }
        
    # Calculate across-track distance
    detection_center_x = bbox_x + (bbox_w / 2.0)
    
    res = range_resolution_m if range_resolution_m is not None else 0.1
    
    if channel == 'starboard':
        across_track_distance = detection_center_x * res
        bearing = ping_heading + 90.0
    else:  # port
        across_track_distance = (image_width - detection_center_x) * res
        bearing = ping_heading - 90.0
        
    # Standardize bearing to 0-360
    bearing = bearing % 360.0
    
    # Slant range correction could be applied here if ping_altitude is present and reliable
    # For now, we assume across_track_distance is horizontal distance as per basic spec.
    horizontal_distance = across_track_distance
    
    # Convert inputs to radians for WGS84 projection
    lat1 = math.radians(ping_latitude)
    lon1 = math.radians(ping_longitude)
    brng = math.radians(bearing)
    d_over_r = horizontal_distance / EARTH_RADIUS_M
    
    # Project point
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d_over_r) + 
        math.cos(lat1) * math.sin(d_over_r) * math.cos(brng)
    )
    
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d_over_r) * math.cos(lat1),
        math.cos(d_over_r) - math.sin(lat1) * math.sin(lat2)
    )
    
    return {
        "geotagging_available": True,
        "latitude": math.degrees(lat2),
        "longitude": math.degrees(lon2)
    }

def geotag_detections(
    detections: list[dict],
    pings: list[dict],
    tile_infos: Optional[list[dict]] = None,
    range_resolution_m: Optional[float] = None,
    channel: str = 'starboard',
    image_width: int = 1024
) -> list[dict]:
    """
    Apply geotagging to a list of detections using a list of ping navigation data.
    
    Args:
        detections: List of detection dicts containing bbox info.
        pings: List of ping navigation dicts (latitude, longitude, heading, etc.).
        tile_infos: Optional list of tile metadata to map bbox to original image coords.
        range_resolution_m: Resolution in meters per pixel.
        channel: 'port' or 'starboard'.
        image_width: Full width of the image.
        
    Returns:
        Updated list of detection dicts with geotagging info.
    """
    num_pings = len(pings)
    if num_pings == 0:
        logger.warning("No pings provided for geotagging.")
        for det in detections:
            det["geotagging_available"] = False
            det["latitude"] = None
            det["longitude"] = None
        return detections
        
    for det in detections:
        # Assuming bbox_y maps directly to ping index in the combined full image
        # If tiling is used, bbox_y needs adjustment. (Simplified here per instructions)
        ping_idx = int(det.get("bbox_y", 0))
        
        # Clamp to valid ping range
        if ping_idx < 0:
            ping_idx = 0
        elif ping_idx >= num_pings:
            ping_idx = num_pings - 1
            
        ping = pings[ping_idx]
        
        geo_info = geotag_detection(
            bbox_x=det["bbox_x"],
            bbox_y=det["bbox_y"],
            bbox_w=det["bbox_w"],
            bbox_h=det["bbox_h"],
            ping_latitude=ping.get("latitude"),
            ping_longitude=ping.get("longitude"),
            ping_heading=ping.get("heading"),
            ping_altitude=ping.get("altitude"),
            range_resolution_m=range_resolution_m,
            channel=channel,
            image_width=image_width
        )
        
        det.update(geo_info)
        det["ping_number"] = ping.get("ping_number", ping_idx)
        det["ping_timestamp"] = ping.get("timestamp")
        
    return detections
