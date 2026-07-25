"""ardkr.storage — R2/S3 객체 경로 계산.

extra: [storage]  (pip install "ardkr[storage]")
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

CHUNK_SIZE = 8 * 1024 * 1024

try:
    from pystac import Collection, Item
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.storage 는 pystac 이 필요합니다: pip install "ardkr[storage]"'
    ) from exc


def _cache_root() -> Path:
    return Path(os.environ.get("ARDKR_CACHE_ROOT", "/cache"))


def s3_cache_dir() -> Path:
    """S3 호환 오브젝트 스토리지의 로컬 미러 루트.

    기본값은 ``<ARDKR_CACHE_ROOT>/s3`` (컨테이너에서는 보통 ``/cache/s3``).
    로컬 파일 경로는 ``s3_cache_dir() / <bucket> / <s3_key>`` 형태다.
    """
    return Path(os.environ.get("ARDKR_S3_CACHE_DIR", str(_cache_root() / "s3")))


def multihash_sha256(data: bytes) -> str:
    """바이트열의 STAC ``file:checksum`` (Multihash, sha2-256)을 반환한다.

    소량 데이터용이다. 큰 파일은 :func:`file_digest`를 쓴다.
    """
    return "1220" + hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> tuple[int, str]:
    """파일을 chunk로 읽으며 ``(size, file:checksum)``을 계산한다.

    ``size``는 읽은 바이트 누적값이고, ``checksum``은 같은 읽기에서 계산한 Multihash다.

    Args:
        path: digest할 로컬 파일 경로.

    Returns:
        ``(size, checksum)`` 튜플.

    Raises:
        FileNotFoundError: 파일이 없을 때.
    """
    if not path.is_file():
        raise FileNotFoundError(f"파일이 없습니다: {path}")

    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
            size += len(chunk)
    return size, "1220" + hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class ObjectPath:
    """R2/S3 객체의 key와 로컬 미러 경로."""

    s3_key: str
    cache_path: Path

    @property
    def file_ext_props(self) -> dict[str, int | str]:
        """``asset.ext.file.apply(**...)``에 넘길 ``checksum``·``size`` kwargs."""
        size, checksum = file_digest(self.cache_path)
        return {"checksum": checksum, "size": size}


def object_path(
    *,
    collection: Collection,
    filename: str,
    item: Item | None = None,
) -> ObjectPath:
    """collection·item·파일명으로 S3 key와 로컬 미러 경로를 계산한다.

    ``s3_key``는 STAC asset ``href``로 쓰고, ``cache_path``는 duckdb 등으로
    쓸 로컬 파일 경로다. ``cache_path``의 부모 디렉터리는 없으면 만든다.

    Args:
        collection: version extension이 적용된 STAC Collection.
        filename: 객체 파일명 (예: ``mdl.parquet``).
        item: STAC Item. 주어지면 key에 ``{item.id}/`` 세그먼트를 넣는다.

    Returns:
        계산된 ``s3_key``와 ``cache_path``.

    Raises:
        ValueError: collection에 version extension이 없을 때.
        KeyError: ``ARDKR_S3_BUCKET_NAME`` 환경변수가 없을 때.
    """
    version = collection.ext.version.version
    if not version:
        raise ValueError("collection에 version extension이 없습니다.")

    if item is None:
        s3_key = f"{collection.id}/version={version}/{filename}"
    else:
        s3_key = f"{collection.id}/version={version}/{item.id}/{filename}"

    bucket = os.environ["ARDKR_S3_BUCKET_NAME"]
    cache_path = s3_cache_dir() / bucket / s3_key
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    return ObjectPath(s3_key=s3_key, cache_path=cache_path)
