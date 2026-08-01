"""ardkr.pipeline — collection lifecycle framework.

extra: [pipeline]  (pip install "ardkr[pipeline]")

Process scripts declare STAC metadata, transform sources into products, and
verify. Paths, digests, publish, and lifecycle are enforced here.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

from pystac import (
    Asset,
    Catalog,
    CatalogType,
    Collection,
    Item,
    Link,
    MediaType,
)

from ..storage import Scope, get_client, get_credentials

try:
    from botocore.exceptions import ClientError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.pipeline requires boto3: pip install "ardkr[pipeline]"'
    ) from exc

ACCESSOR = "kr"
HASH_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
ROOT_CATALOG_ID = "ardkr"


def _s3_cache_dir() -> Path:
    root = Path(os.environ.get("ARDKR_CACHE_ROOT", "/cache"))
    return Path(os.environ.get("ARDKR_S3_CACHE_DIR", str(root / "s3")))


def _parse_s3_href(href: str) -> tuple[str, str]:
    """Parse ``s3://bucket/key`` into ``(bucket, key)``."""
    parsed = urlparse(href)
    return parsed.netloc, parsed.path.lstrip("/")


def _catalog_id(collection: Collection) -> str:
    parent = collection.get_parent()
    return parent.id if parent is not None else ROOT_CATALOG_ID


def _collection_version(collection: Collection) -> str:
    version = collection.ext.version.version
    if not version:
        raise ValueError("collection is missing the version extension")
    return version


def _asset_scope(asset: Asset) -> Scope:
    roles = asset.roles or []
    return Scope.OPEN if "thumbnail" in roles else Scope.S3


def _load_or_create_root_catalog(
    client, bucket: str, key: str, catalog_id: str
) -> Catalog:
    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NoSuchBucket"):
            return Catalog(
                id=catalog_id,
                # Published catalog copy (Korean); not package documentation.
                description="연구팀 공공 공간데이터 STAC 카탈로그.",
                title="ardkr 공간데이터 카탈로그",
            )
        raise
    return Catalog.from_dict(json.loads(response["Body"].read().decode("utf-8")))


class CollectionBuilder(ABC):
    """Lifecycle: process → verify_auto → verify_manual → publish."""

    @property
    @abstractmethod
    def collection(self) -> Collection:
        """Target STAC Collection."""
        ...

    @abstractmethod
    def process(self) -> None:
        """Process data and metadata."""
        ...

    @abstractmethod
    def verify_auto(self) -> None:
        """Run automatic checks. Raise on failure."""
        ...

    @property
    @abstractmethod
    def manual_checklist(self) -> dict[str, bool]:
        """Manual checklist. False means unsigned → build stops."""
        ...

    @classmethod
    def build(cls) -> None:
        instance = cls()
        instance.process()
        instance.verify_auto()
        instance.verify_manual()
        instance.publish()

    def verify_manual(self) -> None:
        failed = [q for q, ok in self.manual_checklist.items() if not ok]
        if failed:
            raise ValueError(
                "Unsigned manual checklist items. Flip to True to sign off.\n"
                + "\n".join(failed)
            )

    def publish(self) -> None:
        if self.collection.ext.version.experimental:
            raise ValueError(
                "collection is experimental. "
                "Set experimental=False when ready to publish, then rerun."
            )

        for asset in self.collection.assets.values():
            asset.kr.publish()

        for item in self.collection.get_items(recursive=True):
            for asset in item.assets.values():
                asset.kr.publish()

        self._publish_stac()

    def _publish_stac(self) -> None:
        """Upload the collection as static self-contained STAC to the open bucket
        and refresh the root catalog.
        """
        collection = self.collection
        version = _collection_version(collection)
        catalog_id = _catalog_id(collection)
        creds = get_credentials(Scope.OPEN)
        client = get_client(Scope.OPEN)
        version_segment = f"version={version}"
        prefix = f"{catalog_id}/{collection.id}/{version_segment}"

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / collection.id / version_segment
            collection.normalize_and_save(
                f"{out_dir}/", catalog_type=CatalogType.SELF_CONTAINED
            )
            for path in out_dir.rglob("*"):
                if not path.is_file():
                    continue
                key = f"{prefix}/{path.relative_to(out_dir).as_posix()}"
                content_type = (
                    MediaType.JSON
                    if path.suffix == ".json"
                    else "application/octet-stream"
                )
                with path.open("rb") as body:
                    client.put_object(
                        Bucket=creds.bucket_name,
                        Key=key,
                        Body=body,
                        ContentType=content_type,
                    )

        catalog_key = f"{catalog_id}/catalog.json"
        catalog = _load_or_create_root_catalog(
            client, creds.bucket_name, catalog_key, catalog_id
        )
        child_prefix = f"./{collection.id}/"
        catalog.links = [
            link
            for link in catalog.links
            if not (
                link.rel == "child"
                and link.href
                and link.href.startswith(child_prefix)
            )
        ]
        catalog.add_link(
            Link(
                rel="child",
                target=f"./{collection.id}/{version_segment}/collection.json",
                media_type=MediaType.JSON,
                title=collection.title or collection.id,
            )
        )
        body = json.dumps(
            catalog.to_dict(transform_hrefs=False),
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        client.put_object(
            Bucket=creds.bucket_name,
            Key=catalog_key,
            Body=body,
            ContentType=MediaType.JSON,
        )


class Accessor[T]:
    def __init__(self, obj: T) -> None:
        self._obj = obj

    @property
    def obj(self) -> T:
        return self._obj


def register_accessor(cls: type):
    def decorator(accessor_cls):
        setattr(cls, ACCESSOR, property(lambda self: accessor_cls(self)))
        return accessor_cls

    return decorator


@register_accessor(Collection)
class CollectionAccessor(Accessor[Collection]):
    def asset_href(self, filename: str, *, scope: Scope = Scope.S3) -> str:
        """Build an ``s3://`` href for a collection-level asset."""
        collection = self._obj
        version = _collection_version(collection)
        bucket = get_credentials(scope).bucket_name
        catalog_id = _catalog_id(collection)
        return (
            f"s3://{bucket}/{catalog_id}/{collection.id}/"
            f"version={version}/assets/{filename}"
        )


@register_accessor(Item)
class ItemAccessor(Accessor[Item]):
    def asset_href(self, filename: str, *, scope: Scope = Scope.S3) -> str:
        """Build an ``s3://`` href for an item-level asset."""
        item = self._obj
        collection = item.get_parent()
        if not isinstance(collection, Collection):
            raise TypeError("item parent must be a Collection")
        version = _collection_version(collection)
        bucket = get_credentials(scope).bucket_name
        catalog_id = _catalog_id(collection)
        return (
            f"s3://{bucket}/{catalog_id}/{collection.id}/"
            f"version={version}/items/{item.id}/assets/{filename}"
        )


@register_accessor(Asset)
class AssetAccessor(Accessor[Asset]):
    
    @property
    def path(self) -> Path:
        """Local mirror path. Creates parent directories if missing."""
        bucket, key = _parse_s3_href(self._obj.href)
        path = _s3_cache_dir() / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def local_digest(self) -> tuple[int, str]:
        """``(size, file:checksum)`` of the local mirror file."""
        path = self.path
        if not path.is_file():
            raise FileNotFoundError(f"file not found: {path}")
        hasher = hashlib.sha256()
        size = 0
        with path.open("rb") as f:
            while chunk := f.read(HASH_CHUNK_SIZE):
                hasher.update(chunk)
                size += len(chunk)
        return size, "1220" + hasher.hexdigest()

    def remote_digest(self) -> tuple[int, str] | None:
        """Remote ``(size, checksum)``, or None if missing."""
        bucket, key = _parse_s3_href(self._obj.href)
        client = get_client(_asset_scope(self._obj))
        try:
            response = client.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return None
            raise
        checksum = response.get("Metadata", {}).get("checksum")
        if not checksum:
            return None
        return response["ContentLength"], checksum

    def publish(self) -> None:
        """Write digest onto the file extension; upload if remote differs."""
        asset = self._obj
        size, checksum = self.local_digest()
        if not asset.ext.has("file"):
            asset.ext.add("file")
        asset.ext.file.apply(size=size, checksum=checksum)

        if self.remote_digest() == (size, checksum):
            return

        bucket, key = _parse_s3_href(asset.href)
        put_kwargs: dict[str, object] = {"Metadata": {"checksum": checksum}}
        if asset.media_type:
            put_kwargs["ContentType"] = asset.media_type

        client = get_client(_asset_scope(asset))
        with self.path.open("rb") as body:
            client.put_object(Bucket=bucket, Key=key, Body=body, **put_kwargs)
