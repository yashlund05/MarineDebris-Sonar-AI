import pytest
import numpy as np
import csv
from backend.sonar_parser.models import SonarFrame, SonarPing, SonarMetadata
from backend.ingestion.ingestor import ingest_survey
from backend.ingestion.image_loader import load_png_strip
from backend.ingestion.nav_csv_parser import parse_nav_csv
from PIL import Image

def test_sonar_frame_creation():
    ping = SonarPing(ping_number=1, timestamp=100.0, latitude=45.0, longitude=-120.0, pixel_y=0)
    meta = SonarMetadata(frequency_hz=900000, samples_per_ping=100)
    arr = np.zeros((1, 100), dtype=np.float32)
    
    frame = SonarFrame(
        survey_id="test_survey",
        source_file="test.png",
        channel="starboard",
        chunk_index=0,
        ping_offset=0,
        pings=[ping],
        image_array=arr,
        metadata=meta
    )
    
    assert frame.survey_id == "test_survey"
    assert len(frame.pings) == 1
    assert frame.image_array.shape == (1, 100)
    assert frame.metadata.frequency_hz == 900000

def test_sonar_ping_defaults():
    ping = SonarPing(ping_number=1, timestamp=100.0)
    assert ping.latitude is None
    assert ping.longitude is None
    assert ping.pitch is None
    assert ping.is_dropout is False
    assert ping.pixel_y == 0

def test_png_loader_synthetic(tmp_path):
    img_path = tmp_path / "test.png"
    arr = np.ones((500, 100), dtype=np.uint8) * 128
    Image.fromarray(arr).save(img_path)
    
    gen = load_png_strip(str(img_path), "test_survey", chunk_size=200)
    frames = list(gen)
    
    assert len(frames) == 3
    assert frames[0].image_array.shape == (200, 100)
    assert frames[1].image_array.shape == (200, 100)
    assert frames[2].image_array.shape == (100, 100)
    
    # Check normalization
    assert np.isclose(frames[0].image_array[0, 0], 128 / 255.0, atol=1e-2)

def test_ingestor_routing_png(tmp_path):
    img_path = tmp_path / "test.png"
    arr = np.ones((10, 10), dtype=np.uint8)
    Image.fromarray(arr).save(img_path)
    
    gen = ingest_survey(str(img_path), "png", "test_survey")
    frames = list(gen)
    assert len(frames) == 1

def test_ingestor_routing_jsf_raises():
    with pytest.raises(NotImplementedError):
        list(ingest_survey("test.jsf", "jsf", "test_survey"))

def test_ingestor_routing_tiff_raises():
    with pytest.raises(NotImplementedError):
        list(ingest_survey("test.tiff", "tiff", "test_survey"))

def test_nav_csv_parser(tmp_path):
    csv_path = tmp_path / "nav.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ping_number', 'timestamp', 'latitude', 'longitude', 'heading', 'altitude', 'range_m', 'pitch', 'roll'])
        writer.writerow(['1', '100.0', '45.0', '-120.0', '180.0', '10.0', '50.0', '0.1', '0.2'])
        writer.writerow(['2', '101.0', '45.1', '-120.1', '', '', '', '', ''])
        
    data = parse_nav_csv(str(csv_path))
    assert len(data) == 2
    assert data[0]['ping_number'] == 1
    assert data[0]['latitude'] == 45.0
    assert data[1]['ping_number'] == 2
    assert data[1]['heading'] is None
