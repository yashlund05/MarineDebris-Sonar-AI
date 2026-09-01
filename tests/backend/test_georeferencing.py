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


def test_geotag_cardinal_headings_and_port_channel():
    """Verify WGS84 geodesy across all 4 cardinal headings and port/starboard symmetry."""
    base_lat = 10.0
    base_lon = 50.0

    # 1. Heading 0 (North), Starboard -> projects East (lon increases, lat ~ unchanged)
    sb_north = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=base_lat, ping_longitude=base_lon,
        ping_heading=0.0, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert sb_north["longitude"] > base_lon
    assert abs(sb_north["latitude"] - base_lat) < 1e-4

    # 2. Heading 0 (North), Port -> projects West (lon decreases, lat ~ unchanged)
    port_north = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=base_lat, ping_longitude=base_lon,
        ping_heading=0.0, ping_altitude=None,
        range_resolution_m=0.1, channel='port', image_width=1024
    )
    assert port_north["longitude"] < base_lon
    assert abs(port_north["latitude"] - base_lat) < 1e-4

    # 3. Heading 90 (East), Starboard -> projects South (lat decreases)
    sb_east = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=base_lat, ping_longitude=base_lon,
        ping_heading=90.0, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert sb_east["latitude"] < base_lat

    # 4. Heading 180 (South), Starboard -> projects West (lon decreases)
    sb_south = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=base_lat, ping_longitude=base_lon,
        ping_heading=180.0, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert sb_south["longitude"] < base_lon

    # 5. Heading 270 (West), Starboard -> projects North (lat increases)
    sb_west = geotag_detection(
        bbox_x=50, bbox_y=0, bbox_w=100, bbox_h=100,
        ping_latitude=base_lat, ping_longitude=base_lon,
        ping_heading=270.0, ping_altitude=None,
        range_resolution_m=0.1, channel='starboard', image_width=1024
    )
    assert sb_west["latitude"] > base_lat
