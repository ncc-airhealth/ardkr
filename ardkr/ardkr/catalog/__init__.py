"""Local Git-managed STAC catalog registration."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pystac
from pystac.layout import TemplateLayoutStrategy
from pystac.stac_io import DefaultStacIO

CATALOG_ROOT_ENV = "ARDKR_CATALOG_ROOT"

_root_catalog: pystac.Catalog | None = None
_root_catalog_path: Path | None = None
_LAYOUT_STRATEGY = TemplateLayoutStrategy(
    collection_template="${id}/${version}/collection.json",
    item_template="items/${id}/item.json",
)


class _Utf8StacIO(DefaultStacIO):
    """Serialize STAC JSON as readable UTF-8 text."""

    def json_dumps(self, json_dict, *args, **kwargs) -> str:
        kwargs.setdefault("indent", 2)
        kwargs["ensure_ascii"] = False
        return json.dumps(json_dict, *args, **kwargs)


def _catalog_root() -> Path:
    value = os.environ.get(CATALOG_ROOT_ENV)
    if not value:
        raise RuntimeError(
            f"{CATALOG_ROOT_ENV} 환경변수가 필요합니다. "
            "Git catalog 디렉터리를 지정하세요."
        )

    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"catalog 디렉터리가 없습니다: {path}")
    return path


def _load_root_catalog() -> pystac.Catalog:
    root = _catalog_root()
    href = root / "catalog.json"
    if not href.is_file():
        raise FileNotFoundError(
            f"수동으로 생성한 root catalog가 없습니다: {href}"
        )

    try:
        return pystac.Catalog.from_file(str(href))
    except Exception as exc:
        raise ValueError(f"root catalog를 읽을 수 없습니다: {href}") from exc


def get_root_catalog() -> pystac.Catalog:
    global _root_catalog, _root_catalog_path

    root = _catalog_root()
    if _root_catalog is None or _root_catalog_path != root:
        _root_catalog = _load_root_catalog()
        _root_catalog_path = root
    return _root_catalog


def _child_id(link: pystac.Link) -> str | None:
    if link.is_resolved() and isinstance(
        link.target, (pystac.Catalog, pystac.Collection)
    ):
        return link.target.id

    href = link.get_href(transform_href=False)
    if not href:
        return None
    href = href.removeprefix("./")
    return href.split("/", 1)[0] or None


def register_collection(collection: pystac.Collection) -> None:
    root = get_root_catalog()

    if any(
        _child_id(link) == collection.id for link in root.get_links("child")
    ):
        root.remove_child(collection.id)

    root.add_child(collection)
    root.normalize_and_save(
        str(_catalog_root()),
        catalog_type=pystac.CatalogType.RELATIVE_PUBLISHED,
        strategy=_LAYOUT_STRATEGY,
        stac_io=_Utf8StacIO(),
    )


__all__ = ["get_root_catalog", "register_collection"]
