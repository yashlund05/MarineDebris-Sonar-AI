"""
MarineDebris-Sonar-AI: Verifiable Dataset Acquisition Engine
Downloads genuine, peer-reviewed acoustic sonar imagery and annotations
from official research repositories into datasets/sonar_debris_v3/raw/.
Logs complete transfer metadata to reports/dataset_expansion/acquisition_log.jsonl.
"""

import os
import sys
import json
import time
import hashlib
import urllib.request
import concurrent.futures
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone

BASE_WATERTANK_URL = (
    "https://raw.githubusercontent.com/mvaldenegro/marine-debris-fls-datasets/master"
    "/md_fls_dataset/data/watertank-segmentation"
)
BASE_QUARRY_URL = (
    "https://raw.githubusercontent.com/mvaldenegro/marine-debris-fls-datasets/master"
    "/md_fls_dataset/data/quarry-fullsize"
)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def fetch_url(url: str, dest: Path, max_retries: int = 3) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MarineDebrisSonarAI-Acquire/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                if len(content) == 0:
                    continue
                with open(dest, "wb") as f:
                    f.write(content)
                return True
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return False


class DatasetAcquirer:
    def __init__(
        self,
        raw_root: Path = Path("datasets/sonar_debris_v3/raw"),
        log_file: Path = Path("reports/dataset_expansion/acquisition_log.jsonl"),
    ):
        self.raw_root = Path(raw_root)
        self.log_file = Path(log_file)
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_acquisition(self, entry: Dict[str, Any]):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def acquire_watertank_expansion(
        self,
        start_idx: int = 0,
        end_idx: int = 650,
        max_workers: int = 16,
    ) -> Dict[str, Any]:
        """
        Acquires real ARIS Explorer 3000 watertank sonar frames and annotations.
        """
        dataset_id = "md_fls_watertank"
        dest_dir = self.raw_root / dataset_id
        img_dest = dest_dir / "Images"
        xml_dest = dest_dir / "BoxAnnotations"
        img_dest.mkdir(parents=True, exist_ok=True)
        xml_dest.mkdir(parents=True, exist_ok=True)

        tasks = []
        for idx in range(start_idx, end_idx):
            img_name = f"marine-debris-aris3k-{idx}.png"
            xml_name = f"marine-debris-aris3k-{idx}.xml"
            img_url = f"{BASE_WATERTANK_URL}/Images/{img_name}"
            xml_url = f"{BASE_WATERTANK_URL}/BoxAnnotations/{xml_name}"

            tasks.append((img_url, img_dest / img_name, "image"))
            tasks.append((xml_url, xml_dest / xml_name, "annotation"))

        print(f"[ACQUIRE] Downloading {len(tasks)} files for {dataset_id} (indices {start_idx} to {end_idx - 1})...")
        t0 = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_url, url, path): (url, path, kind) for url, path, kind in tasks}
            downloaded = 0
            for f in concurrent.futures.as_completed(futures):
                if f.result():
                    downloaded += 1

        duration = round(time.perf_counter() - t0, 2)
        print(f"[ACQUIRE] Completed {downloaded}/{len(tasks)} files in {duration}s.")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_id": dataset_id,
            "source_url": BASE_WATERTANK_URL,
            "doi": "10.5281/zenodo.15101686",
            "license": "CC-BY 4.0",
            "requested_items": len(tasks),
            "downloaded_items": downloaded,
            "duration_seconds": duration,
            "status": "SUCCESS" if downloaded >= int(len(tasks) * 0.90) else "PARTIAL",
        }
        self.log_acquisition(result)
        return result

    def acquire_quarry_negatives(
        self,
        sequence_names: Optional[List[str]] = None,
        frames_per_sequence: int = 10,
        max_workers: int = 12,
    ) -> Dict[str, Any]:
        """
        Acquires real flooded quarry background frames as authentic negative/background seabed samples.
        """
        dataset_id = "md_fls_quarry_field_negatives"
        dest_dir = self.raw_root / dataset_id / "Images"
        dest_dir.mkdir(parents=True, exist_ok=True)

        if sequence_names is None:
            sequence_names = [
                "2016-06-22_113541",
                "2016-06-22_114714",
                "2016-06-22_143000",
                "2016-06-22_143319",
                "2016-06-22_143818",
                "2016-06-22_144047",
            ]

        tasks = []
        for seq in sequence_names:
            for f_idx in range(frames_per_sequence):
                fname = f"{seq}-frame{f_idx:05d}.png"
                url = f"{BASE_QUARRY_URL}/{seq}/{fname}"
                tasks.append((url, dest_dir / fname))

        print(f"[ACQUIRE] Downloading {len(tasks)} genuine negative seabed frames from {len(sequence_names)} quarry sequences...")
        t0 = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_url, url, path) for url, path in tasks]
            downloaded = sum(1 for f in concurrent.futures.as_completed(futures) if f.result())

        duration = round(time.perf_counter() - t0, 2)
        print(f"[ACQUIRE] Completed {downloaded}/{len(tasks)} negative seabed frames in {duration}s.")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_id": dataset_id,
            "source_url": BASE_QUARRY_URL,
            "doi": "10.5281/zenodo.15101686",
            "license": "CC-BY 4.0",
            "requested_items": len(tasks),
            "downloaded_items": downloaded,
            "duration_seconds": duration,
            "is_negative": True,
            "status": "SUCCESS" if downloaded >= int(len(tasks) * 0.80) else "PARTIAL",
        }
        self.log_acquisition(result)
        return result


if __name__ == "__main__":
    acq = DatasetAcquirer()
    # Acquire up to 600 watertank frames + 60 quarry negative frames
    acq.acquire_watertank_expansion(start_idx=0, end_idx=600)
    acq.acquire_quarry_negatives(frames_per_sequence=10)
