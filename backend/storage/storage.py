"""File storage abstraction supporting local filesystem and S3-compatible (MinIO) backends.

Provides a unified interface so the rest of the application does not care whether
files are stored locally or in MinIO.  See ARCHITECTURAL_BLUEPRINT.md §10.
"""

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional

from backend.config import get_settings


class StorageBackend(ABC):
    """Abstract base class for file storage backends."""

    @abstractmethod
    def save_file(
        self,
        file_data: BinaryIO,
        relative_path: str,
        *,
        filename: Optional[str] = None,
    ) -> str:
        """Save a file and return its storage path relative to the storage root.

        Args:
            file_data: Binary file-like object to save.
            relative_path: Directory path relative to storage root (e.g. "surveys/uuid").
            filename: Optional filename override; auto-generated if not provided.

        Returns:
            The full relative storage path of the saved file.
        """
        ...

    @abstractmethod
    def get_file_path(self, relative_path: str) -> str:
        """Return the absolute filesystem path for a stored file.

        Args:
            relative_path: Path relative to storage root.

        Returns:
            Absolute path to the file on disk.
        """
        ...

    @abstractmethod
    def read_file(self, relative_path: str) -> bytes:
        """Read and return the contents of a stored file.

        Args:
            relative_path: Path relative to storage root.

        Returns:
            File contents as bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Delete a stored file.

        Args:
            relative_path: Path relative to storage root.

        Returns:
            True if the file was deleted, False if it did not exist.
        """
        ...

    @abstractmethod
    def file_exists(self, relative_path: str) -> bool:
        """Check whether a file exists in storage.

        Args:
            relative_path: Path relative to storage root.

        Returns:
            True if the file exists.
        """
        ...

    @abstractmethod
    def get_download_path(self, relative_path: str) -> str:
        """Return a path or URL suitable for downloading/serving the file.

        For local storage this is the absolute path; for MinIO it could be a presigned URL.
        """
        ...


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, root_dir: str) -> None:
        """Initialize local storage with the given root directory.

        Args:
            root_dir: Absolute or relative path to the storage root directory.
        """
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        """Resolve a relative path to an absolute path within the storage root.

        Prevents path traversal attacks by ensuring the resolved path is under root.
        """
        resolved = (self.root / relative_path).resolve()
        # Security: ensure resolved path is under storage root
        if not str(resolved).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return resolved

    def save_file(
        self,
        file_data: BinaryIO,
        relative_path: str,
        *,
        filename: Optional[str] = None,
    ) -> str:
        """Save a file to local filesystem."""
        target_dir = self._resolve(relative_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"{uuid.uuid4().hex}"

        file_path = target_dir / filename
        with open(file_path, "wb") as f:
            # Stream in chunks to avoid loading entire file into memory
            chunk_size = 8 * 1024 * 1024  # 8 MB chunks
            while True:
                chunk = file_data.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)

        # Return path relative to storage root
        return str(file_path.relative_to(self.root))

    def get_file_path(self, relative_path: str) -> str:
        """Return absolute path for a stored file."""
        return str(self._resolve(relative_path))

    def read_file(self, relative_path: str) -> bytes:
        """Read file contents from local filesystem."""
        file_path = self._resolve(relative_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return file_path.read_bytes()

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file from local filesystem."""
        file_path = self._resolve(relative_path)
        if file_path.is_file():
            file_path.unlink()
            return True
        if file_path.is_dir():
            shutil.rmtree(file_path)
            return True
        return False

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists on local filesystem."""
        return self._resolve(relative_path).exists()

    def get_download_path(self, relative_path: str) -> str:
        """Return absolute path for download/serving."""
        return self.get_file_path(relative_path)


# ---------------------------------------------------------------------------
# Singleton storage instance
# ---------------------------------------------------------------------------

_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Return the configured storage backend singleton.

    Uses STORAGE_TYPE from settings to determine which backend to use:
    - "local" → LocalStorage
    - "minio" → MinIO (raises NotImplementedError until implemented)

    Returns:
        StorageBackend instance.
    """
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    settings = get_settings()
    storage_type = settings.STORAGE_TYPE.lower()

    if storage_type == "local":
        _storage_instance = LocalStorage(root_dir=settings.storage_root_path)
    elif storage_type == "minio":
        # MinIO support is architecturally planned but not yet implemented
        raise NotImplementedError(
            "MinIO storage backend is not yet implemented. "
            "Set STORAGE_TYPE=local for local filesystem storage."
        )
    else:
        raise ValueError(f"Unknown storage type: {storage_type}. Use 'local' or 'minio'.")

    return _storage_instance


def reset_storage() -> None:
    """Reset the storage singleton (used in tests)."""
    global _storage_instance
    _storage_instance = None
