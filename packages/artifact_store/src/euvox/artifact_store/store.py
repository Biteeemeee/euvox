from __future__ import annotations

import asyncio
import hashlib
import io
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ArtifactStore(Protocol):
    async def upload_bytes(self, bucket: str, key: str, data: bytes) -> str:
        """Upload bytes; return the canonical URI for the stored object."""
        ...

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        ...

    async def exists(self, bucket: str, key: str) -> bool:
        ...


class LocalArtifactStore:
    """File-system backed store — used in tests and local dev without MinIO."""

    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir

    def _path(self, bucket: str, key: str) -> Path:
        return self._base / bucket / key

    async def upload_bytes(self, bucket: str, key: str, data: bytes) -> str:
        path = self._path(bucket, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"file://{path}"

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        return self._path(bucket, key).read_bytes()

    async def exists(self, bucket: str, key: str) -> bool:
        return self._path(bucket, key).exists()


class MinioArtifactStore:
    """MinIO (S3-compatible) artifact store backed by the `minio` Python client."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        *,
        secure: bool = False,
    ) -> None:
        from minio import Minio  # type: ignore[import-untyped]

        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def _ensure_bucket(self, bucket: str) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    async def upload_bytes(self, bucket: str, key: str, data: bytes) -> str:
        def _upload() -> str:
            self._ensure_bucket(bucket)
            self._client.put_object(bucket, key, io.BytesIO(data), length=len(data))
            return f"s3://{bucket}/{key}"

        return await asyncio.to_thread(_upload)

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        def _download() -> bytes:
            response = self._client.get_object(bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await asyncio.to_thread(_download)

    async def exists(self, bucket: str, key: str) -> bool:
        def _exists() -> bool:
            try:
                self._client.stat_object(bucket, key)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_exists)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
