"""
MarineDebris-Sonar-AI: Sequence-Aware Group Splitter & Leakage Auditor
Partitions sonar frames strictly by continuous sequence / recording block.
Enforces zero temporal or spatial sequence leakage across train, val, and test splits.
"""

from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import re


class SequenceAwareSplitter:
    def __init__(self, block_size: int = 20):
        self.block_size = block_size

    def extract_sequence_id(self, filename: str) -> str:
        """
        Extracts continuous sequence identifier from filename.
        Examples:
            'marine-debris-aris3k-55.png' -> block id based on index // block_size
            '2016-06-22_113541-frame00005.png' -> '2016-06-22_113541'
            'turntable_bottle_deg045.png' -> 'turntable_bottle'
        """
        # 1. Check timestamped quarry format
        quarry_match = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{6})", filename)
        if quarry_match:
            return quarry_match.group(1)

        # 2. Check turntable format
        if "turntable" in filename:
            parts = filename.split("_")
            if len(parts) >= 2:
                return f"turntable_{parts[1]}"

        # 3. Check aris3k index format
        aris_match = re.match(r"marine-debris-aris3k-(\d+)", filename)
        if aris_match:
            idx = int(aris_match.group(1))
            block_num = idx // self.block_size
            return f"aris3k_seq_block_{block_num:03d}"

        # Fallback: file stem
        return Path(filename).stem

    def partition_samples_by_sequence(
        self,
        samples: List[Dict[str, Any]],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups samples by sequence_id and allocates entire sequence groups
        into train, val, and test splits to guarantee zero sequence leakage.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for s in samples:
            seq_id = s.get("sequence_id") or self.extract_sequence_id(s["filename"])
            s["sequence_id"] = seq_id
            grouped.setdefault(seq_id, []).append(s)

        seq_ids = sorted(list(grouped.keys()))
        total_samples = len(samples)

        target_train = int(total_samples * train_ratio)
        target_val = int(total_samples * val_ratio)

        train_samples = []
        val_samples = []
        test_samples = []

        # Allocate entire sequence groups
        for seq_id in seq_ids:
            group_items = grouped[seq_id]
            if len(train_samples) + len(group_items) <= target_train or (not val_samples and len(train_samples) < target_train):
                train_samples.extend(group_items)
            elif len(val_samples) + len(group_items) <= target_val or (not test_samples and len(val_samples) < target_val):
                val_samples.extend(group_items)
            else:
                test_samples.extend(group_items)

        return {
            "train": train_samples,
            "val": val_samples,
            "test": test_samples,
        }

    @staticmethod
    def audit_leakage(splits: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Audits train, val, and test splits for any overlapping sequences or exact filenames.
        """
        seq_sets = {
            k: {s["sequence_id"] for s in v}
            for k, v in splits.items()
        }
        file_sets = {
            k: {s["filename"] for s in v}
            for k, v in splits.items()
        }

        train_val_seq = sorted(list(seq_sets.get("train", set()) & seq_sets.get("val", set())))
        train_test_seq = sorted(list(seq_sets.get("train", set()) & seq_sets.get("test", set())))
        val_test_seq = sorted(list(seq_sets.get("val", set()) & seq_sets.get("test", set())))

        train_val_files = sorted(list(file_sets.get("train", set()) & file_sets.get("val", set())))
        train_test_files = sorted(list(file_sets.get("train", set()) & file_sets.get("test", set())))
        val_test_files = sorted(list(file_sets.get("val", set()) & file_sets.get("test", set())))

        has_leakage = bool(train_val_seq or train_test_seq or val_test_seq or train_val_files or train_test_files or val_test_files)

        return {
            "sequence_overlap": {
                "train_vs_val": train_val_seq,
                "train_vs_test": train_test_seq,
                "val_vs_test": val_test_seq,
            },
            "filename_overlap": {
                "train_vs_val": train_val_files,
                "train_vs_test": train_test_files,
                "val_vs_test": val_test_files,
            },
            "leakage_detected": has_leakage,
            "status": "FAIL" if has_leakage else "PASS",
        }
