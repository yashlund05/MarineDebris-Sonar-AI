from typing import Generator, Optional
from backend.sonar_parser.models import SonarFrame
from backend.sonar_parser.xtf_parser import parse_xtf
from backend.sonar_parser.jsf_parser import parse_jsf
from backend.ingestion.image_loader import load_png_strip
from backend.ingestion.nav_csv_parser import parse_nav_csv

def ingest_survey(file_path: str, file_type: str, survey_id: str, channel: str = 'starboard', chunk_size: int = 2000, nav_csv_path: Optional[str] = None) -> Generator[SonarFrame, None, None]:
    file_type = file_type.lower()
    
    if file_type == 'xtf':
        yield from parse_xtf(file_path, survey_id, chunk_size, channel)
    elif file_type == 'png':
        nav_data = None
        if nav_csv_path:
            nav_data = parse_nav_csv(nav_csv_path)
        yield from load_png_strip(file_path, survey_id, channel, chunk_size, nav_data)
    elif file_type in ['jsf', 'tiff']:
        if file_type == 'jsf':
            yield from parse_jsf(file_path, survey_id)
        else:
            raise NotImplementedError(f"{file_type.upper()} format parsing is deferred to V1. See PRD.md §4.1.")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
