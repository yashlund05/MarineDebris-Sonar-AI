"""Empirical performance benchmark runner for MarineDebris-Sonar-AI pipeline stages."""

import time
import tempfile
import numpy as np
from pathlib import Path

from backend.sonar_parser.models import SonarFrame, SonarPing, SonarMetadata
from backend.preprocessing.quality import assess_quality
from backend.preprocessing.bottom_detection import detect_bottom
from backend.preprocessing.water_column import remove_water_column
from backend.preprocessing.normalization import normalize
from backend.preprocessing.clahe import apply_clahe
from backend.preprocessing.denoising import denoise
from backend.preprocessing.tiler import generate_tiles
from backend.inference.detector import RawDetection
from backend.postprocessing.nms import apply_global_nms
from backend.postprocessing.size_filter import filter_by_size
from backend.postprocessing.calibration import calibrate_confidence
from backend.georeferencing.geotagger import geotag_detection
from backend.reporting.json_reporter import generate_json_report
from backend.reporting.csv_reporter import generate_csv_report
from backend.reporting.geojson_reporter import generate_geojson_report


def run_benchmark():
    print("==============================================================================")
    print("           MARINEDEBRIS-SONAR-AI PIPELINE EMPIRICAL BENCHMARK                 ")
    print("==============================================================================")

    # 1. Benchmark Synthetic Sonar Strip: 2,000 pings x 1,024 columns (float32)
    H, W = 2000, 1024
    raw_strip = np.random.uniform(0.05, 0.95, (H, W)).astype(np.float32)
    pings = [
        SonarPing(ping_number=i, timestamp=float(i) * 0.1, latitude=18.92 + (i * 0.00001), longitude=72.83 + (i * 0.00001), heading=45.0)
        for i in range(H)
    ]
    frame = SonarFrame(
        survey_id="bench-001",
        source_file="benchmark.png",
        channel="starboard",
        chunk_index=0,
        ping_offset=0,
        pings=pings,
        image_array=raw_strip,
        metadata=SonarMetadata(frequency_hz=455000.0, samples_per_ping=W, range_resolution_m=0.075),
    )

    # Stage A: Quality Assessment
    t0 = time.perf_counter()
    assess_quality(frame)
    t_quality = (time.perf_counter() - t0) * 1000

    # Stage B: Bottom Detection
    t0 = time.perf_counter()
    bottom_line = detect_bottom(raw_strip)
    t_bottom = (time.perf_counter() - t0) * 1000

    # Stage C: Water Column Removal
    t0 = time.perf_counter()
    wcr_strip = remove_water_column(raw_strip, bottom_line)
    t_wcr = (time.perf_counter() - t0) * 1000

    # Stage D: Normalization
    t0 = time.perf_counter()
    norm_strip = normalize(wcr_strip)
    t_norm = (time.perf_counter() - t0) * 1000

    # Stage E: CLAHE
    t0 = time.perf_counter()
    clahe_strip = apply_clahe(norm_strip)
    t_clahe = (time.perf_counter() - t0) * 1000

    # Stage F: Denoising (Median Filter)
    t0 = time.perf_counter()
    denoised_strip = denoise(clahe_strip, method="median", kernel_size=3)
    t_denoise = (time.perf_counter() - t0) * 1000

    # Stage G: Tiling (640x640 with 20% overlap)
    t0 = time.perf_counter()
    tiles = generate_tiles(denoised_strip, tile_size=640, overlap=0.2)
    t_tiling = (time.perf_counter() - t0) * 1000

    total_prep_ms = t_quality + t_bottom + t_wcr + t_norm + t_clahe + t_denoise + t_tiling

    # 2. Benchmark Post-processing (100 synthetic detections)
    raw_dets = []
    for i in range(100):
        raw_dets.append(
            RawDetection(
                class_id=i % 5,
                class_name="derelict_fishing_gear",
                confidence=0.5 + ((i % 50) * 0.01),
                bbox_x=(i * 15) % 900,
                bbox_y=(i * 18) % 1800,
                bbox_w=40,
                bbox_h=40,
                tile_row=i // 10,
                tile_col=i % 10,
            )
        )

    # NMS
    t0 = time.perf_counter()
    nms_survived = apply_global_nms(raw_dets, iou_threshold=0.45)
    t_nms = (time.perf_counter() - t0) * 1000

    # Size filter
    t0 = time.perf_counter()
    sized = filter_by_size(nms_survived, min_area_px=100, max_area_px=50000)
    t_size = (time.perf_counter() - t0) * 1000

    # Calibration
    t0 = time.perf_counter()
    calibrated = calibrate_confidence(sized, temperature=1.4)
    t_calib = (time.perf_counter() - t0) * 1000

    # Georeferencing (100 calculations)
    t0 = time.perf_counter()
    for det in calibrated:
        geotag_detection(
            bbox_x=det.bbox_x,
            bbox_y=det.bbox_y,
            bbox_w=det.bbox_w,
            bbox_h=det.bbox_h,
            ping_latitude=18.9220,
            ping_longitude=72.8347,
            ping_heading=45.0,
            ping_altitude=15.0,
            range_resolution_m=0.075,
            channel="starboard",
            image_width=1024,
        )
    t_georef = (time.perf_counter() - t0) * 1000

    # 3. Benchmark Reporting Generation (JSON, CSV, GeoJSON)
    sample_dets = [
        {
            "id": f"det-{i}",
            "detection_code": f"D{i:05d}",
            "class_name": "derelict_fishing_gear",
            "confidence": 0.85,
            "confidence_calibrated": 0.82,
            "bbox_x": 100,
            "bbox_y": 200,
            "bbox_w": 40,
            "bbox_h": 40,
            "geotagging_available": True,
            "latitude": 18.922 + (i * 0.0001),
            "longitude": 72.834 + (i * 0.0001),
            "ping_number": i,
            "ping_timestamp": float(i),
            "is_filtered": False,
            "filtered_reason": None,
        }
        for i in range(50)
    ]
    survey_info = {"id": "bench-survey-001", "source_filename": "benchmark.png", "created_at": "2026-09-01T00:00:00Z"}

    with tempfile.TemporaryDirectory() as tmpdir:
        p_json = Path(tmpdir) / "report.json"
        p_csv = Path(tmpdir) / "report.csv"
        p_geojson = Path(tmpdir) / "report.geojson"

        t0 = time.perf_counter()
        generate_json_report(sample_dets, survey_info, str(p_json))
        t_json = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        generate_csv_report(sample_dets, str(p_csv))
        t_csv = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        generate_geojson_report(sample_dets, str(p_geojson))
        t_geojson = (time.perf_counter() - t0) * 1000

    print(f"[*] Input Resolution:            {H} pings x {W} samples ({raw_strip.nbytes / (1024*1024):.2f} MB float32)")
    print(f"[*] Generated Tiles (640x640):   {len(tiles)} tiles")
    print(f"[-] Quality Assessment:          {t_quality:.2f} ms")
    print(f"[-] Bottom Line Detection:       {t_bottom:.2f} ms")
    print(f"[-] Water Column Removal:        {t_wcr:.2f} ms")
    print(f"[-] Intensity Normalization:     {t_norm:.2f} ms")
    print(f"[-] CLAHE Contrast Enhancement:  {t_clahe:.2f} ms")
    print(f"[-] Median Filter Denoising:     {t_denoise:.2f} ms")
    print(f"[-] Tile Grid Slicing:           {t_tiling:.2f} ms")
    print(f"[+] Total Preprocessing Time:    {total_prep_ms:.2f} ms ({total_prep_ms/1000:.3f} s)")
    print("------------------------------------------------------------------------------")
    print(f"[-] Global NMS (100 boxes):      {t_nms:.2f} ms")
    print(f"[-] Bounding Box Area Filter:    {t_size:.2f} ms")
    print(f"[-] Temperature Calibration:     {t_calib:.2f} ms")
    print(f"[-] WGS84 Geodesy (100 points):  {t_georef:.2f} ms")
    print("------------------------------------------------------------------------------")
    print(f"[-] JSON Report Generation:      {t_json:.2f} ms")
    print(f"[-] CSV Report Generation:       {t_csv:.2f} ms")
    print(f"[-] GeoJSON FeatureCollection:   {t_geojson:.2f} ms")
    print("==============================================================================")


if __name__ == "__main__":
    run_benchmark()
