"""Collection lifecycle implementation for :mod:`ardkr.pipeline`."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pystac import Collection

from .. import catalog
from . import pystac_pipe_accessor  # noqa: F401


class CollectionBuilder(ABC):
    collection: Collection
    checklist: dict[str, bool]

    def __init__(self):
        self.collection.ext.add("file")
        self.collection.ext.add("version")
        catalog.get_root_catalog().add_child(self.collection)

    @classmethod
    def build(cls) -> None:
        obj = cls()
        obj.process()
        obj.verify_auto()
        obj.verify_manual()
        obj.publish()

    @abstractmethod
    def process(self) -> None:
        ...

    @abstractmethod
    def verify_auto(self) -> None:
        ...

    def verify_manual(self) -> None:
        for q, a in self.checklist.items():
            if not a:
                raise ValueError(f"confrim checklist : `{q}`")

    def publish(self) -> None:
        self.collection.validate()
        for item in self.collection.get_items(recursive=True):
            item.validate()

        catalog.register_collection(self.collection)

        if self.collection.ext.version.experimental:
            raise ValueError("Publish blocked: `experimental=False`")

        for asset in self.collection.pipe.iter_assets():
            print(f"publishing: `{asset.href}`")
            asset.pipe.publish()
