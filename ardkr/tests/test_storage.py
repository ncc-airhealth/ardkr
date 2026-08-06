"""Real S3 integration tests for :mod:`ardkr.storage`.

The repository root ``.env`` is loaded before importing ``ardkr.storage``.
The round-trip test creates and removes its own remote object.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _load_root_env() -> None:
    env_file = REPOSITORY_ROOT / ".env"
    if not env_file.is_file():
        return

    for raw_line in env_file.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()

        name, separator, value = line.partition("=")
        if not separator:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name.strip(), value)


_load_root_env()

_REQUIRED_ENV = (
    "ARDKR_S3_CACHE_DIR",
    "ARDKR_PRIVATE_BUCKET_NAME",
    "ARDKR_PRIVATE_ENDPOINT_URL",
    "ARDKR_PRIVATE_ACCESS_KEY_ID",
    "ARDKR_PRIVATE_SECRET_ACCESS_KEY",
    "ARDKR_OPEN_BUCKET_NAME",
    "ARDKR_OPEN_ENDPOINT_URL",
    "ARDKR_OPEN_ACCESS_KEY_ID",
    "ARDKR_OPEN_SECRET_ACCESS_KEY",
)


def _storage_module():
    missing = [name for name in _REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "real S3 integration test requires environment: "
            + ", ".join(missing)
        )

    from ardkr import storage

    return storage


def test_head_returns_none_for_missing_object() -> None:
    storage = _storage_module()
    bucket = storage.get_bucket_name("private")
    href = f"s3://{bucket}/.ardkr-test/missing/{uuid4().hex}"

    assert storage.head(href) is None


def test_head_rejects_unconfigured_https_href() -> None:
    storage = _storage_module()

    with pytest.raises(ValueError, match="unconfigured public href"):
        storage.head("https://example.com/object")


def test_upload_head_download_round_trip() -> None:
    storage = _storage_module()
    bucket = storage.get_bucket_name("private")
    key = f".ardkr-test/round-trip/{uuid4().hex}.txt"
    href = f"s3://{bucket}/{key}"
    content = b"ardkr real storage round-trip\n"

    with TemporaryDirectory() as directory:
        source = Path(directory) / "source.txt"
        target = Path(directory) / "downloaded.txt"
        source.write_bytes(content)

        try:
            storage.upload(source, href)

            metadata = storage.head(href)
            assert metadata is not None
            assert metadata["size"] == len(content)
            assert metadata["checksum"] == (
                "1220"
                + hashlib.sha256(content).hexdigest()
            )

            assert storage.download(href, target) == target
            assert target.read_bytes() == content
        finally:
            storage.get_client("private").delete_object(
                Bucket=bucket,
                Key=key,
            )


def test_asset_path_downloads_and_refreshes_cache() -> None:
    storage = _storage_module()
    from pystac import Asset

    import ardkr.pipeline.pystac_pipe_accessor  # noqa: F401

    bucket = storage.get_bucket_name("private")
    key = f".ardkr-test/asset-path/{uuid4().hex}.txt"
    href = f"s3://{bucket}/{key}"
    content = b"ardkr asset cache round-trip\n"

    with TemporaryDirectory() as directory:
        source = Path(directory) / "source.txt"
        source.write_bytes(content)
        cache_path = storage.cache_path(href)

        try:
            storage.upload(source, href)

            asset = Asset(href=href)
            assert asset.pipe.remote_digest() == {
                "size": len(content),
                "checksum": (
                    "1220" + hashlib.sha256(content).hexdigest()
                ),
            }
            assert asset.pipe.path(download=True) == cache_path
            assert cache_path.read_bytes() == content

            cache_path.write_bytes(b"corrupted cache")
            assert asset.pipe.path(download=True) == cache_path
            assert cache_path.read_bytes() == content
        finally:
            storage.get_client("private").delete_object(
                Bucket=bucket,
                Key=key,
            )
            cache_path.unlink(missing_ok=True)


def test_asset_publish_is_idempotent_and_rejects_conflicts() -> None:
    storage = _storage_module()
    from pystac import Asset, Item

    import ardkr.pipeline.pystac_pipe_accessor  # noqa: F401

    bucket = storage.get_bucket_name("private")
    key = f".ardkr-test/publish/{uuid4().hex}.txt"
    href = f"s3://{bucket}/{key}"
    original = b"ardkr publish original\n"
    conflicting = b"ardkr publish conflicting\n"

    with TemporaryDirectory():
        cache_path = storage.cache_path(href)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cache_path.write_bytes(original)
            item = Item(
                id=f"publish-{uuid4().hex}",
                geometry=None,
                bbox=None,
                datetime=datetime(2020, 1, 1, tzinfo=UTC),
                properties={},
            )
            asset = Asset(href=href)
            item.add_asset("data", asset)
            asset.ext.add("file")
            asset.pipe.apply_digest()

            asset.pipe.publish()
            assert storage.head(href) == asset.pipe.digest()

            asset.pipe.publish()

            cache_path.write_bytes(conflicting)
            conflicting_item = Item(
                id=f"publish-conflict-{uuid4().hex}",
                geometry=None,
                bbox=None,
                datetime=datetime(2020, 1, 1, tzinfo=UTC),
                properties={},
            )
            conflicting_asset = Asset(href=href)
            conflicting_item.add_asset("data", conflicting_asset)
            conflicting_asset.ext.add("file")
            conflicting_asset.pipe.apply_digest()
            with pytest.raises(ValueError, match="remote digest mismatch"):
                conflicting_asset.pipe.publish()
        finally:
            storage.get_client("private").delete_object(
                Bucket=bucket,
                Key=key,
            )
            cache_path.unlink(missing_ok=True)
