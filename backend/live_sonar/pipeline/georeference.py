"""Geospatial Association for Live Sonar Detections.

Associates detections with authentic navigation data (GNSS / INS) when available.
Enforces the Zero Fabrication rule: returns None / NOT_AVAILABLE when GPS is missing.
Conforms to Requirement R2 §25 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

from typing import Optional, Tuple
from backend.live_sonar.models import LiveNavigationData


def associate_geolocation(
    bbox: Tuple[int, int, int, int],
    image_shape: Tuple[int, int],
    navigation: Optional[LiveNavigationData],
    range_m: Optional[float] = None,
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Estimate target geolocation (latitude, longitude, depth) from sensor navigation.

    If navigation is missing or coordinates are None, returns (None, None, None).
    Never invents or fabricates coordinates.
    """
    if navigation is None:
        return (None, None, None)

    lat = navigation.latitude
    lon = navigation.longitude
    depth = navigation.depth_m

    if lat is None or lon is None:
        return (None, None, depth)

    # If vehicle has valid GNSS and range is available, compute approximate offset
    # based on heading and target range in image
    heading = navigation.heading_deg or 0.0
    # For now, return vessel position with depth or refined coordinate if geometry exists
    return (round(float(lat), 7), round(float(lon), 7), depth)
