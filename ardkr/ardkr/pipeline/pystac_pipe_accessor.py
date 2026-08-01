"""Internal ``.pipe`` accessors for PySTAC objects."""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path

from pystac import Asset, Collection, Item

from .. import storage

ACCESSOR = "pipe"
HASH_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB


def register_accessor(cls: type):
    def decorator(accessor_cls):
        setattr(cls, ACCESSOR, property(lambda self: accessor_cls(self)))
        return accessor_cls

    return decorator


class Accessor[T]:
    def __init__(self, obj: T) -> None:
        self._obj = obj


def _collection_asset_href(
    collection: Collection, store: str, filename: str
) -> str:
    catalog_id = collection.get_parent().id
    version = collection.ext.version.version
    bucket = storage.get_bucket_name(store)
    return (
        f"s3://{bucket}/{catalog_id}/{collection.id}/{version}/"
        f"assets/{filename}"
    )


def _item_asset_href(item: Item, store: str, filename: str) -> str:
    collection = item.get_parent()
    if not isinstance(collection, Collection):
        raise TypeError(f"item `{item.id}` must be attached to a collection")

    catalog_id = collection.get_parent().id
    version = collection.ext.version.version
    bucket = storage.get_bucket_name(store)
    return (
        f"s3://{bucket}/{catalog_id}/{collection.id}/{version}/"
        f"items/{item.id}/assets/{filename}"
    )


@register_accessor(Collection)
class CollectionAccessor(Accessor[Collection]):
    def define_asset(
        self,
        store: str = "private",
        key: str | None = None,
        filename: str | None = None,
        **kwargs,
    ) -> Asset:
        if key is None or filename is None:
            raise TypeError("define_asset() requires `key` and `filename`")

        href = _collection_asset_href(self._obj, store, filename)
        asset = Asset(href=href, **kwargs)
        self._obj.add_asset(key, asset)
        return asset

    def iter_assets(self) -> Iterator[Asset]:
        yield from self._obj.assets.values()
        for item in self._obj.get_items(recursive=True):
            yield from item.assets.values()


@register_accessor(Item)
class ItemAccessor(Accessor[Item]):
    def define_asset(
        self,
        store: str = "private",
        key: str | None = None,
        filename: str | None = None,
        **kwargs,
    ) -> Asset:
        if key is None or filename is None:
            raise TypeError("define_asset() requires `key` and `filename`")

        href = _item_asset_href(self._obj, store, filename)
        asset = Asset(href=href, **kwargs)
        self._obj.add_asset(key, asset)
        return asset


@register_accessor(Asset)
class AssetAccessor(Accessor[Asset]):
    def path(self, download: bool = False) -> Path:
        local_path = storage.cache_path(self._obj.href)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if download and (
            not local_path.is_file()
            or self.local_digest() != self.remote_digest()
        ):
            storage.download(self._obj.href, local_path)

        return local_path

    def apply_digest(self) -> None:
        digest = self.local_digest()
        self._obj.ext.file.apply(**digest)

    def publish(self) -> None:
        expected = self.digest()
        local = self.local_digest()
        assert expected == local, f"asset digest mismatch: {self._obj.href}"
        
        remote = storage.head(self._obj.href)
        if remote is not None:
            if remote != expected:
                raise ValueError(f"remote digest mismatch: {self._obj.href}")
            return
        
        storage.upload(self.path(), self._obj.href)

    def digest(self) -> dict:
        return {
            "size": self._obj.ext.file.size,
            "checksum": self._obj.ext.file.checksum,
        }

    def local_digest(self) -> dict:
        path = self.path()
        if not path.is_file():
            raise FileNotFoundError(f"file not found: {path}")

        size, hasher = 0, hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(HASH_CHUNK_SIZE):
                size += len(chunk)
                hasher.update(chunk)

        checksum = "1220" + hasher.hexdigest()
        return {"size": size, "checksum": checksum}

    def remote_digest(self) -> dict:
        metadata = storage.head(self._obj.href)
        if metadata is None:
            message = f"remote object not found: {self._obj.href}"
            raise FileNotFoundError(message)

        if not metadata["checksum"]:
            message = f"remote object has no checksum: {self._obj.href}"
            raise ValueError(message)
        return {
            "size": metadata["size"], 
            "checksum": metadata["checksum"],
        }
