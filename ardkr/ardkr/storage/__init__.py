"""ardkr.storage — R2/S3 객체 경로·업로드·STAC 등록.

extra: [storage]  (pip install "ardkr[storage]")
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pystac

CHUNK_SIZE = 8 * 1024 * 1024

try:
    from pystac import Asset, Collection, Item
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.storage 는 pystac 이 필요합니다: pip install "ardkr[storage]"'
    ) from exc

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.storage 는 boto3 가 필요합니다: pip install "ardkr[storage]"'
    ) from exc

from pystac.extensions.file import FileExtension


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


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["ARDKR_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["ARDKR_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["ARDKR_S3_SECRET_ACCESS_KEY"],
    )


def remote_checksum(key: str, *, client=None) -> str | None:
    """R2 객체의 커스텀 메타데이터 ``checksum``을 HEAD 요청만으로 읽는다.

    Args:
        key: S3 객체 key.
        client: 재사용할 boto3 S3 client. 생략 시 새로 만든다.

    Returns:
        checksum 문자열. 객체가 없으면 ``None``.
    """
    if client is None:
        client = _s3_client()
    bucket = os.environ["ARDKR_S3_BUCKET_NAME"]
    try:
        response = client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return None
        raise
    return response.get("Metadata", {}).get("checksum")


def _asset_checksum(asset: Asset) -> str:
    checksum = FileExtension.ext(asset, add_if_missing=False).checksum
    if not checksum:
        raise ValueError(f"asset에 file:checksum이 없습니다: {asset.href}")
    return checksum


def _upload_asset(asset: Asset, key: str, checksum: str, *, client) -> None:
    bucket = os.environ["ARDKR_S3_BUCKET_NAME"]
    cache_path = s3_cache_dir() / bucket / key
    if not cache_path.is_file():
        raise FileNotFoundError(f"업로드할 로컬 파일이 없습니다: {cache_path}")

    put_kwargs: dict[str, object] = {"Metadata": {"checksum": checksum}}
    if asset.media_type:
        put_kwargs["ContentType"] = asset.media_type

    with cache_path.open("rb") as body:
        client.put_object(Bucket=bucket, Key=key, Body=body, **put_kwargs)


def _upload_collection_assets(collection: Collection) -> None:
    client = _s3_client()
    for item in collection.get_items():
        for asset in item.assets.values():
            key = asset.href
            if not key or "://" in key:
                raise ValueError(f"asset href는 S3 key여야 합니다: {key!r}")
            checksum = _asset_checksum(asset)
            if remote_checksum(key, client=client) != checksum:
                _upload_asset(asset, key, checksum, client=client)


def _save_stac_catalog(
    collection: Collection, version: str, catalog_root: str | Path
) -> None:
    """collection을 ``stac-metadata/``에 self-contained로 저장하고 루트 catalog를 갱신한다."""
    catalog_root = Path(catalog_root).resolve()
    version_segment = f"version={version}"
    collection_dir = catalog_root / collection.id / version_segment
    collection.normalize_and_save(
        f"{collection_dir}/", catalog_type=pystac.CatalogType.SELF_CONTAINED
    )

    catalog_path = catalog_root / "catalog.json"
    catalog_json = json.loads(catalog_path.read_text(encoding="utf-8"))
    prefix = f"./{collection.id}/"
    catalog_json["links"] = [
        link
        for link in catalog_json["links"]
        if not (link.get("rel") == "child" and link.get("href", "").startswith(prefix))
    ]
    catalog_json["links"].append(
        {
            "rel": "child",
            "href": f"{prefix}{version_segment}/collection.json",
            "type": "application/json",
            "title": collection.title or collection.id,
        }
    )
    catalog_path.write_text(
        json.dumps(catalog_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for json_path in catalog_root.rglob("*.json"):
        if json_path == catalog_path:
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def register_collection(
    collection: Collection, catalog_root: str | Path = "stac-metadata"
) -> None:
    """collection을 STAC 카탈로그에 등록하고, 필요 시 R2 asset을 업로드한다.

    ``collection.ext.version``의 ``experimental``이 ``False``이면 item·asset을 순회하며
    원격 ``checksum`` 메타데이터와 asset ``file:checksum``을 비교해, 객체가 없거나
    불일치할 때만 로컬 캐시에서 단일 ``put_object``로 업로드한다. 그다음
    ``catalog_root``(기본 ``stac-metadata/``)에 collection·item STAC을 저장한다.
    ``experimental``이 ``True``이면 STAC 저장만 한다.

    ``catalog_root``는 내부에서만 절대경로로 변환하고, 저장되는 link·href는 상대경로다.

    Args:
        collection: version extension이 적용된 STAC Collection. item은
            ``collection.add_item``으로 등록되어 있어야 한다.
        catalog_root: STAC 메타데이터 루트. 기본값은 cwd 기준 ``stac-metadata``.

    Raises:
        ValueError: version extension·file:checksum·asset href가 유효하지 않을 때.
        FileNotFoundError: 업로드할 로컬 캐시 파일이 없을 때.
        KeyError: 필요한 ``ARDKR_S3_*`` 환경변수가 없을 때.
    """
    version = collection.ext.version.version
    if not version:
        raise ValueError("collection에 version extension이 없습니다.")

    if not collection.ext.version.experimental:
        _upload_collection_assets(collection)

    _save_stac_catalog(collection, version, catalog_root)
