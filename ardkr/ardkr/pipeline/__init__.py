from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar
from warnings import warn

from pystac import Asset, Collection, Item

from ..common import Secrets

T = TypeVar("T")
ACCESSOR = "kr"
HASH_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB


class CollectionBuilder(ABC):
     
    @property
    @abstractmethod
    def collection(self) -> Collection:
        """collection object."""
        ...
    
    @abstractmethod
    def process(self):
        """Process the collection data & metadata."""
        ...

    @abstractmethod
    def verify_auto(self):
        """Verify the collection data & metadata automatically."""
        ...
    
    @property
    @abstractmethod
    def manual_checklist(self) -> dict[str, bool]:
        """Manual checklist(key: yes or no question, value: answer)."""
        ...
    
    @classmethod 
    def build(cls):
        c = cls()
        c.process()
        c.verify_auto()
        c.verify_manual()
        c.publish()
    
    def verify_manual(self):
        checklist = []
        for q, a in self.manual_checklist.items():
            if not a:
                checklist.append(q)
        if checklist:
            raise ValueError(f"\n## 수동 검증 항목 실패\n{'\n'.join(checklist)}\n")
    
    def publish(self):
        if self.collection.ext.version.experimental:
            raise ValueError(
                "The collection is experimental.\n"
                "If ready, set `experimental` as False and run again."
            )
        
        for asset in self.collection.assets.values():
            asset.kr.publish()
        
        for item in self.collection.get_item(recursive=True):
            for asset in item.assets.values():
                asset.kr.publish()


class Accessor(Generic[T]):
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


@register_accessor
class CollectionAccessor:
    def __init__(self, obj: Collection):
        self._obj = obj


@register_accessor
class ItemAccessor:
    def __init__(self, obj: Item):
        self._obj = obj


@register_accessor
class AssetAccessor:
    def __init__(self, obj: Asset):
        self._obj = obj
    

    def make_href(self, filename: str) -> str:
        owner = self._obj.owner
        prefix = f"s3://{Secrets().S3_BUCKET_NAME}"
        if isinstance(owner, Collection):
            collection = owner
            version = collection.extra_fields["version"]
            postfix = f"assets/{filename}"
        if isinstance(owner, Item):
            collection = owner.get_parent()
            version = collection.extra_fields["version"]
            postfix = f"items/{owner.id}/assets/{filename}"
        catalog = collection.get_parent()
        parts = [prefix, catalog.id, collection.id, version, postfix]
        return "/".join(parts)

    @property
    def path(self) -> Path:
        return S3_CACHE_PATH / self._obj[len(BUCKET_PREFIX):]
    
    def local_digest(self) -> tuple[int, str]:
        path = self._obj.kr.path
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {self._obj.kr.path}")
        
        size, hasher = 0, hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(HASH_CHUNK_SIZE):
                hasher.update(chunk)
                size += len(chunk)
        
        return size, "1220" + hasher.hexdigest()
    
    def remote_digest(self) -> tuple[int, str]:
    
    @property
    def publish(self):
        asset = self._obj
        asset.ext.add("file")
        asset.ext.file.size, asset.ext.file.checksum = self.digest()
        