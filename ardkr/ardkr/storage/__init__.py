"""ardkr.storage — R2/S3 객체 경로 계산.

extra: [storage]  (pip install "ardkr[storage]")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True, slots=True)
class ObjectPath:
    """R2/S3 객체의 key와 로컬 미러 경로."""

    s3_key: str
    cache_path: Path


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
