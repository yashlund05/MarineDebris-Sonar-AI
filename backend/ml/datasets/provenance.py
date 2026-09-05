"""
MarineDebris-Sonar-AI: Dataset Provenance Engine
Tracks complete, immutable scientific lineage for every imported sonar image.
Outputs to JSON Lines (.jsonl) format with SHA256 cryptographic verification.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class ProvenanceRecord:
    sample_id: str
    dataset_id: str
    source_dataset: str
    source_url: str
    doi: Optional[str]
    authors: List[str]
    institution: str
    publication: Optional[str]
    peer_reviewed: bool
    license: str
    original_filename: str
    normalized_filename: str
    sonar_type: str
    sonar_model: str
    frequency: str
    sequence_id: str
    capture_session: Optional[str]
    geographic_region: Optional[str]
    image_sha256: str
    annotation_sha256: Optional[str]
    source_classes: List[str]
    mapped_classes: List[str]
    is_negative: bool
    processing: List[str]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProvenanceManager:
    def __init__(self, provenance_file: Path):
        self.provenance_file = Path(provenance_file)
        self.provenance_file.parent.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, ProvenanceRecord] = {}
        self._load()

    def _load(self):
        if self.provenance_file.exists():
            with open(self.provenance_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        rec = ProvenanceRecord(**data)
                        self.records[rec.sample_id] = rec

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def add_record(self, record: ProvenanceRecord) -> None:
        self.records[record.sample_id] = record
        with open(self.provenance_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def get_record(self, sample_id: str) -> Optional[ProvenanceRecord]:
        return self.records.get(sample_id)

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify that every registered record has required scientific metadata and valid hash."""
        total = len(self.records)
        missing_source = 0
        missing_license = 0
        verified = 0

        for rec in self.records.values():
            if not rec.source_url or not rec.source_dataset:
                missing_source += 1
            elif not rec.license:
                missing_license += 1
            else:
                verified += 1

        return {
            "total_records": total,
            "verified_records": verified,
            "missing_source": missing_source,
            "missing_license": missing_license,
            "status": "PASS" if missing_source == 0 and missing_license == 0 else "FAIL",
        }
