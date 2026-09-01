import logging
from typing import Generator
import numpy as np
from .models import SonarFrame, SonarPing, SonarMetadata

logger = logging.getLogger(__name__)

def parse_xtf(file_path: str, survey_id: str, chunk_size: int = 2000, channel: str = 'starboard') -> Generator[SonarFrame, None, None]:
    try:
        import pyxtf
    except ImportError:
        logger.error("pyxtf is not installed. Please install it to parse XTF files.")
        raise ImportError("pyxtf is required to parse XTF files.")

    try:
        # Load XTF file
        xtf_data, _ = pyxtf.xtf_read(file_path)
    except Exception as e:
        logger.error(f"Failed to read XTF file {file_path}: {str(e)}")
        raise ValueError(f"Corrupt or invalid XTF file: {file_path}") from e
    
    # Simple mocked up stream parsing
    channel_index = 0 if channel == 'port' else 1
    # Check if channel exists
    if len(xtf_data.get('sonar', [])) <= channel_index:
        logger.warning(f"Channel {channel} not found in XTF, falling back to 0")
        channel_index = 0

    if not xtf_data.get('sonar'):
        return

    sonar_channel = xtf_data['sonar'][channel_index]
    pings_total = len(sonar_channel.data)
    
    metadata = SonarMetadata(
        frequency_hz=getattr(sonar_channel, 'frequency', None),
        samples_per_ping=sonar_channel.data.shape[1] if hasattr(sonar_channel, 'data') else 0,
        range_resolution_m=getattr(sonar_channel, 'slant_range', None) / sonar_channel.data.shape[1] if getattr(sonar_channel, 'slant_range', 0) and hasattr(sonar_channel, 'data') else None
    )

    for chunk_idx, ping_offset in enumerate(range(0, pings_total, chunk_size)):
        end_idx = min(ping_offset + chunk_size, pings_total)
        chunk_data = sonar_channel.data[ping_offset:end_idx]
        
        # normalize
        if chunk_data.dtype != np.float32:
            image_array = chunk_data.astype(np.float32)
        else:
            image_array = chunk_data
            
        max_val = np.max(image_array)
        if max_val > 0:
            image_array /= max_val

        pings = []
        for i in range(ping_offset, end_idx):
            # Extract header data safely
            # Note: pyxtf specific fields
            header = sonar_channel.ping_headers[i] if hasattr(sonar_channel, 'ping_headers') and len(sonar_channel.ping_headers) > i else None
            
            p = SonarPing(
                ping_number=i,
                timestamp=getattr(header, 'Time', float(i)),  # fallback
                latitude=getattr(header, 'SensorYcoordinate', None),
                longitude=getattr(header, 'SensorXcoordinate', None),
                heading=getattr(header, 'SensorHeading', None),
                pitch=getattr(header, 'SensorPitch', None),
                roll=getattr(header, 'SensorRoll', None),
                altitude=getattr(header, 'SensorPrimaryAltitude', None),
                range_m=getattr(header, 'SlantRange', None),
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
