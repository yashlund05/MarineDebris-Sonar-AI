"""
MarineDebris-Sonar-AI: Deduplication and Perceptual Similarity Engine
Computes exact cryptographic SHA256 hashes and perceptual hashes (dHash / pHash)
to detect exact duplicates, near-duplicates, and sequence neighbors.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any, Set
import hashlib
import cv2
import numpy as np


class DatasetDeduplicator:
    def __init__(self, dhash_threshold: int = 4):
        self.dhash_threshold = dhash_threshold

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def compute_dhash(image_path: Path, hash_size: int = 8) -> int:
        """Computes difference hash (dHash) for an acoustic image."""
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Unable to read image for hashing: {image_path}")

        # Resize to (hash_size + 1, hash_size)
        resized = cv2.resize(img, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
        # Compare adjacent columns
        diff = resized[:, 1:] > resized[:, :-1]
        # Convert binary matrix to 64-bit integer
        decimal_val = 0
        for bit in diff.flatten():
            decimal_val = (decimal_val << 1) | int(bit)
        return decimal_val

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        return bin(hash1 ^ hash2).count("1")

    def analyze_dataset_duplicates(
        self,
        image_paths: List[Path],
    ) -> Dict[str, Any]:
        """
        Scans a collection of image paths, cataloging exact and near-duplicates.
        """
        sha_map: Dict[str, List[str]] = {}
        hash_entries: List[Tuple[str, int, str]] = []

        exact_duplicates = []
        near_duplicates = []

        for p in image_paths:
            path_obj = Path(p)
            sha = self.compute_sha256(path_obj)
            sha_map.setdefault(sha, []).append(path_obj.name)

            dhash = self.compute_dhash(path_obj)
            hash_entries.append((path_obj.name, dhash, sha))

        # 1. Exact duplicates by SHA256
        for sha, filenames in sha_map.items():
            if len(filenames) > 1:
                exact_duplicates.append({
                    "sha256": sha,
                    "canonical": filenames[0],
                    "duplicates": filenames[1:],
                })

        # 2. Near duplicates / sequence neighbors by Hamming distance
        n = len(hash_entries)
        for i in range(n):
            name_i, hash_i, sha_i = hash_entries[i]
            for j in range(i + 1, n):
                name_j, hash_j, sha_j = hash_entries[j]
                if sha_i == sha_j:
                    continue  # Already counted in exact duplicates
                dist = self.hamming_distance(hash_i, hash_j)
                if dist <= self.dhash_threshold:
                    near_duplicates.append({
                        "file_a": name_i,
                        "file_b": name_j,
                        "hamming_distance": dist,
                        "type": "NEAR_DUPLICATE_OR_SEQUENCE_NEIGHBOR" if dist <= 2 else "CLOSE_SIMILARITY",
                    })

        return {
            "total_images_scanned": len(image_paths),
            "unique_sha256_count": len(sha_map),
            "exact_duplicate_groups": len(exact_duplicates),
            "exact_duplicate_files_count": sum(len(d["duplicates"]) for d in exact_duplicates),
            "near_duplicate_pairs_count": len(near_duplicates),
            "exact_duplicates": exact_duplicates,
            "near_duplicates": near_duplicates[:50],  # cap reporting
        }
