"""Pure tests for object href building and parsing (no network)."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pystac
import pytest

import ardkr.pipeline.pystac_pipe_accessor  # noqa: F401  (register .pipe)
from ardkr import storage

PUBLIC_BASE = "https://pub-0123456789abcdef0123456789abcdef.r2.dev"


def _make_collection() -> pystac.Collection:
    catalog = pystac.Catalog(id="ardkr", description="test catalog")
    collection = pystac.Collection(
        id="sgis-adm-bnd",
        description="test collection",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
            temporal=pystac.TemporalExtent(
                [[datetime(2020, 1, 1, tzinfo=UTC), None]]
            ),
        ),
        license="proprietary",
    )
    collection.ext.add("version")
    collection.ext.version.version = "3.0.1"
    catalog.add_child(collection)
    return collection


def test_parse_s3_href() -> None:
    bucket = os.environ["ARDKR_PRIVATE_BUCKET_NAME"]
    href = f"s3://{bucket}/ardkr/sgis-adm-bnd/3.0.1/assets/thumbnail.webp"

    assert storage._parse_object_href(href) == (
        bucket,
        "ardkr/sgis-adm-bnd/3.0.1/assets/thumbnail.webp",
    )


def test_parse_public_https_href(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARDKR_OPEN_PUBLIC_URL", PUBLIC_BASE)
    bucket = os.environ["ARDKR_OPEN_BUCKET_NAME"]
    href = f"{PUBLIC_BASE}/ardkr/sgis-adm-bnd/3.0.1/assets/thumbnail.webp"

    assert storage._parse_object_href(href) == (
        bucket,
        "ardkr/sgis-adm-bnd/3.0.1/assets/thumbnail.webp",
    )


def test_parse_https_rejects_unconfigured_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ARDKR_OPEN_PUBLIC_URL", raising=False)

    with pytest.raises(ValueError, match="unconfigured public href"):
        storage._parse_object_href("https://example.com/object")


def test_open_collection_asset_href_is_https(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ARDKR_OPEN_PUBLIC_URL", PUBLIC_BASE)
    collection = _make_collection()

    asset = collection.pipe.define_asset(
        store="open",
        key="thumbnail",
        filename="thumbnail.webp",
    )

    assert asset.href == (
        f"{PUBLIC_BASE}/ardkr/sgis-adm-bnd/3.0.1/assets/thumbnail.webp"
    )


def test_private_collection_asset_href_is_s3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ARDKR_OPEN_PUBLIC_URL", raising=False)
    collection = _make_collection()
    bucket = os.environ["ARDKR_PRIVATE_BUCKET_NAME"]

    asset = collection.pipe.define_asset(
        store="private",
        key="data",
        filename="data.parquet",
    )

    assert asset.href == (
        f"s3://{bucket}/ardkr/sgis-adm-bnd/3.0.1/assets/data.parquet"
    )


def test_open_item_asset_href_is_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARDKR_OPEN_PUBLIC_URL", PUBLIC_BASE)
    collection = _make_collection()
    item = pystac.Item(
        id="sgis-adm-bnd-2020-2q",
        geometry=None,
        bbox=None,
        datetime=datetime(2020, 1, 1, tzinfo=UTC),
        properties={},
    )
    collection.add_item(item)

    asset = item.pipe.define_asset(
        store="open",
        key="thumbnail",
        filename="thumbnail.webp",
    )

    assert asset.href == (
        f"{PUBLIC_BASE}/ardkr/sgis-adm-bnd/3.0.1/"
        "items/sgis-adm-bnd-2020-2q/assets/thumbnail.webp"
    )
