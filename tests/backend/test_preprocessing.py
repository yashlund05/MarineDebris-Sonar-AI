import pytest
import numpy as np
from backend.sonar_parser.models import SonarFrame, SonarPing, SonarMetadata
from backend.preprocessing.normalization import normalize
from backend.preprocessing.clahe import apply_clahe
from backend.preprocessing.denoising import denoise
from backend.preprocessing.bottom_detection import detect_bottom
from backend.preprocessing.water_column import remove_water_column
from backend.preprocessing.tiler import generate_tiles
from backend.preprocessing.quality import assess_quality
from backend.preprocessing.pipeline import preprocess_frame

def test_normalize_range():
    img = np.array([[0.0, 50.0], [100.0, 200.0]], dtype=np.float32)
    norm = normalize(img)
    assert np.min(norm) >= 0.0
    assert np.max(norm) <= 1.0

def test_normalize_constant():
    img = np.ones((10, 10), dtype=np.float32) * 50.0
    norm = normalize(img)
    assert np.all(norm == 0.0)

def test_clahe_output_range():
    img = np.random.rand(100, 100).astype(np.float32)
    clahe_img = apply_clahe(img)
    assert np.min(clahe_img) >= 0.0
    assert np.max(clahe_img) <= 1.0

def test_denoise_median():
    img = np.random.rand(50, 50).astype(np.float32)
    denoised = denoise(img, method='median', kernel_size=3)
    assert denoised.shape == img.shape

def test_bottom_detection_synthetic():
    img = np.zeros((100, 50), dtype=np.float32)
    img[40:, :] = 1.0 # Bottom starts at row 40
    bottom = detect_bottom(img)
    assert len(bottom) == 50
    assert np.all(bottom == 40)

def test_water_column_removal():
    img = np.ones((100, 50), dtype=np.float32)
    bottom = np.full(50, 40)
    res = remove_water_column(img, bottom)
    assert np.all(res[:40, :] == 0.0)
    assert np.all(res[40:, :] == 1.0)

def test_tiler_count():
    img = np.zeros((1000, 1000), dtype=np.float32)
    # tile_size=640, overlap=0.2 (stride=512)
    # y: ceil((1000 - 640)/512) + 1 = ceil(360/512)+1 = 1 + 1 = 2
    # x: 2
    # total 4
    tiles = generate_tiles(img, tile_size=640, overlap=0.2)
    assert len(tiles) == 4

def test_tiler_overlap():
    img = np.zeros((1000, 1000), dtype=np.float32)
    tiles = generate_tiles(img, tile_size=640, overlap=0.2)
    # Check offsets
    # tile 0: 0,0
    # tile 1: 0,512
    # tile 2: 512,0
    # tile 3: 512,512
    offsets = [(t.row_offset, t.col_offset) for t in tiles]
    assert (0, 0) in offsets
    assert (0, 512) in offsets
    assert (512, 0) in offsets
    assert (512, 512) in offsets

def test_tiler_metadata():
    img = np.zeros((700, 700), dtype=np.float32)
    tiles = generate_tiles(img, tile_size=640, overlap=0.2, chunk_index=1, ping_offset=100)
    for t in tiles:
        assert t.chunk_index == 1
        assert t.ping_offset == 100
        assert t.tile.shape == (640, 640)

def test_quality_dropout():
    ping1 = SonarPing(ping_number=0, timestamp=0.0, data=np.zeros(10))
    ping2 = SonarPing(ping_number=1, timestamp=1.0, data=np.ones(10))
    frame = SonarFrame(
        survey_id="test",
        source_file="test.png",
        channel="starboard",
        pings=[ping1, ping2],
        metadata=SonarMetadata(),
    )

    frame = assess_quality(frame)
    assert frame.pings[0].is_dropout is True
    assert frame.pings[1].is_dropout is True  # Constant ping is a dropout
    assert frame.metadata.dropout_pct == 1.0


def test_quality_score():
    pings = []
    for i in range(4):
        pings.append(SonarPing(ping_number=i, timestamp=float(i), data=np.random.rand(10)))
    pings.append(SonarPing(ping_number=4, timestamp=4.0, data=np.zeros(10)))
    frame = SonarFrame(
        survey_id="test",
        source_file="test.png",
        channel="starboard",
        pings=pings,
        metadata=SonarMetadata(),
    )

    frame = assess_quality(frame)
    assert frame.metadata.dropout_pct == 0.2
    # score = 1.0 - 0.3*0.2 = 1.0 - 0.06 = 0.94
    assert np.isclose(frame.metadata.motion_quality_score, 0.94)


def test_pipeline_integration():
    pings = []
    for i in range(100):
        data = np.zeros(200, dtype=np.float32)
        data[80:] = np.random.rand(120) * 0.5 + 0.5  # Random seabed
        pings.append(SonarPing(ping_number=i, timestamp=float(i), data=data))
    frame = SonarFrame(
        survey_id="test",
        source_file="test.png",
        channel="starboard",
        pings=pings,
        metadata=SonarMetadata(),
    )

    out_frame, tiles = preprocess_frame(frame)
    assert out_frame is not None
    assert len(tiles) > 0
    # Processed tiles should exist and be valid floats
    for t in tiles:
        assert t.tile.dtype == np.float32
