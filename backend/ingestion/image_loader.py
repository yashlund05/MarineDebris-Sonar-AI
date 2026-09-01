import logging
from typing import Generator, Optional
import numpy as np
from PIL import Image
from backend.sonar_parser.models import SonarFrame, SonarPing, SonarMetadata

logger = logging.getLogger(__name__)

def load_png_strip(file_path: str, survey_id: str, channel: str = 'starboard', chunk_size: int = 2000, nav_data: Optional[list] = None) -> Generator[SonarFrame, None, None]:
    try:
        img = Image.open(file_path)
        img = img.convert("L")  # Grayscale
        data = np.array(img, dtype=np.float32) / 255.0
    except Exception as e:
        logger.error(f"Failed to load PNG {file_path}: {e}")
        raise

    height, width = data.shape
    metadata = SonarMetadata(samples_per_ping=width)

    for chunk_idx, ping_offset in enumerate(range(0, height, chunk_size)):
        end_idx = min(ping_offset + chunk_size, height)
        image_array = data[ping_offset:end_idx]

        pings = []
        for i in range(ping_offset, end_idx):
            nav = {}
            if nav_data and i < len(nav_data):
                nav = nav_data[i]

            p = SonarPing(
                ping_number=nav.get('ping_number', i),
                timestamp=nav.get('timestamp', float(i)),
                latitude=nav.get('latitude'),
                longitude=nav.get('longitude'),
                heading=nav.get('heading'),
                pitch=nav.get('pitch'),
                roll=nav.get('roll'),
                altitude=nav.get('altitude'),
                range_m=nav.get('range_m'),
                pixel_y=i - ping_offset
            )
            pings.append(p)

        yield SonarFrame(
            survey_id=survey_id,
            source_file=file_path,
            channel=channel,
            chunk_index=chunk_idx,
            ping_offset=ping_offset,
            pings=pings,
            image_array=image_array,
            metadata=metadata
        )
