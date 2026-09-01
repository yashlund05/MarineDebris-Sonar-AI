import csv
import logging

logger = logging.getLogger(__name__)

def parse_nav_csv(csv_path: str) -> list[dict]:
    nav_data = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed_row = {
                    'ping_number': int(row['ping_number']) if row.get('ping_number') else None,
                    'timestamp': float(row['timestamp']) if row.get('timestamp') else None,
                    'latitude': float(row['latitude']) if row.get('latitude') else None,
                    'longitude': float(row['longitude']) if row.get('longitude') else None,
                    'heading': float(row['heading']) if row.get('heading') else None,
                    'altitude': float(row['altitude']) if row.get('altitude') else None,
                    'range_m': float(row['range_m']) if row.get('range_m') else None,
                    'pitch': float(row['pitch']) if row.get('pitch') else None,
                    'roll': float(row['roll']) if row.get('roll') else None,
                }
                nav_data.append(parsed_row)
    except Exception as e:
        logger.error(f"Failed to parse nav CSV {csv_path}: {e}")
        raise
    return nav_data
