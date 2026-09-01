import math
from backend.georeferencing.geotagger import geotag_detection, geotag_detections
from backend.georeferencing.dimension_estimator import estimate_dimensions

def test_geotag_with_nav_data():
    # known lat/lon, heading
    lat1 = 30.0
    lon1 = -90.0
    heading = 0.0 # moving North
    # Starboard, so 90 deg bearing (East)
    # distance = 100 pixels * 0.1 m/pixel = 10 meters
    result = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=lat1, ping_longitude=lon1,
        ping_heading=heading, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert result["geotagging_available"] is True
    assert result["latitude"] is not None
    assert result["longitude"] is not None
    
    # Very roughly, 10m East at 30N latitude
    # 1 degree of lat = 111km, so 10m is very small lat change (should be ~0 if moving perfectly East)
    assert abs(result["latitude"] - 30.0) < 1e-4
    assert result["longitude"] > -90.0 # moving East increases longitude

def test_geotag_without_nav_data():
    result = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=None, ping_longitude=None,
        ping_heading=None, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert result["geotagging_available"] is False
    assert result["latitude"] is None
    assert result["longitude"] is None

def test_dimension_estimation():
    res = estimate_dimensions(bbox_w=100, bbox_h=50, range_resolution_m=0.1, along_track_resolution_m=0.2)
    assert res["estimated_width_m"] == 10.0
    assert res["estimated_length_m"] == 10.0

def test_dimension_estimation_no_resolution():
    res = estimate_dimensions(bbox_w=100, bbox_h=50, range_resolution_m=None, along_track_resolution_m=None)
    assert res["estimated_width_m"] is None
    assert res["estimated_length_m"] is None
