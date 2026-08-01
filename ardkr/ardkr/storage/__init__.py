"""ardkr.storage — thin S3-compatible connection layer.

extra: [storage]  (pip install "ardkr[storage]")

Provides S3 metadata and download operations. Path scheme, STAC metadata,
upload conventions, and publishing belong to ``ardkr.pipeline``. A ``sign``
helper (presigned URLs) may be added later.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from ..common import S3Credentials, Secrets

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.storage requires boto3: pip install "ardkr[storage]"'
    ) from exc


class Store(StrEnum):
    """Logical object stores exposed to pipeline code."""

    PRIVATE = "private"
    OPEN = "open"


_BUCKET_ENV = {
    Store.PRIVATE: "ARDKR_PRIVATE_BUCKET_NAME",
    Store.OPEN: "ARDKR_OPEN_BUCKET_NAME",
}

S3_CACHE_DIR = Path(os.environ["ARDKR_S3_CACHE_DIR"])


def _parse_s3_href(href: str) -> tuple[str, str]:
    """Parse an ``s3://bucket/key`` href."""
    parsed = urlparse(href)
    key = parsed.path.lstrip("/")
    if parsed.scheme != "s3" or not parsed.netloc or not key:
        raise ValueError(f"invalid S3 href: {href!r}")
    return parsed.netloc, key


def cache_path(href: str) -> Path:
    """Map an ``s3://bucket/key`` href to its local cache path."""
    bucket, key = _parse_s3_href(href)
    return S3_CACHE_DIR / bucket / key


def get_bucket_name(store: str | Store = Store.PRIVATE) -> str:
    """Resolve a logical store to its configured bucket name."""
    try:
        store = Store(store)
    except (TypeError, ValueError) as exc:
        expected = ", ".join(item.value for item in Store)
        raise ValueError(
            f"unknown store {store!r}; expected one of: {expected}"
        ) from exc

    env_name = _BUCKET_ENV[store]
    bucket_name = os.environ.get(env_name)
    if not bucket_name:
        raise RuntimeError(f"{env_name} 환경변수가 필요합니다.")
    return bucket_name


def _store_for_bucket(bucket_name: str) -> Store:
    for store, env_name in _BUCKET_ENV.items():
        if os.environ.get(env_name) == bucket_name:
            return store
    raise ValueError(f"bucket is not configured: {bucket_name!r}")


def upload(source: Path, href: str) -> None:
    """Upload a local file and store its SHA-256 multihash metadata."""
    bucket, key = _parse_s3_href(href)
    store = _store_for_bucket(bucket)
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)

    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)

    client = get_client(store)
    client.upload_file(
        str(source),
        bucket,
        key,
        ExtraArgs={"Metadata": {"checksum": "1220" + digest.hexdigest()}},
    )


def head(href: str) -> dict[str, int | str | None] | None:
    """Return remote object metadata without downloading its body."""
    bucket, key = _parse_s3_href(href)
    store = _store_for_bucket(bucket)
    client = get_client(store)

    try:
        response = client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NoSuchBucket", "NotFound"}:
            return None
        raise

    return {
        "size": response["ContentLength"],
        "checksum": response.get("Metadata", {}).get("checksum"),
    }


def download(href: str, target: Path) -> Path:
    """Download an object to ``target`` after verifying its checksum.

    The object is written to a temporary file in the target directory. The
    existing target is replaced only after the complete download has the
    expected SHA-256 multihash (``1220`` + SHA-256 hex digest).
    """
    bucket, key = _parse_s3_href(href)
    store = _store_for_bucket(bucket)
    metadata = head(href)
    if metadata is None:
        raise FileNotFoundError(f"remote object not found: {href!r}")

    expected_checksum = metadata["checksum"]
    if not expected_checksum:
        raise ValueError(f"remote object has no checksum metadata: {href!r}")

    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)

    try:
        client = get_client(store)
        response = client.get_object(Bucket=bucket, Key=key)
        body = response["Body"]
        digest = hashlib.sha256()
        try:
            with temporary.open("wb") as stream:
                while chunk := body.read(1024 * 1024):
                    stream.write(chunk)
                    digest.update(chunk)
        finally:
            body.close()

        actual_checksum = "1220" + digest.hexdigest()
        if actual_checksum != expected_checksum:
            raise ValueError(
                f"remote checksum mismatch for {href!r}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )

        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def get_credentials(store: str | Store = Store.PRIVATE) -> S3Credentials:
    """Return credentials for ``store``.

    Args:
        store: Logical store. Defaults to the private store.

    Returns:
        Credentials for that store.
    """
    try:
        store = Store(store)
    except (TypeError, ValueError) as exc:
        expected = ", ".join(item.value for item in Store)
        raise ValueError(
            f"unknown store {store!r}; expected one of: {expected}"
        ) from exc

    secrets = Secrets()
    if store == Store.PRIVATE:
        return secrets.private
    return secrets.open


def get_client(store: str | Store = Store.PRIVATE):
    """Return a boto3 S3 client for ``store``.

    Args:
        store: Logical store to connect to. Defaults to the private store.

    Returns:
        Configured boto3 S3 client.
    """
    creds = get_credentials(store)
    return boto3.client(
        "s3",
        endpoint_url=creds.endpoint_url,
        region_name="auto",
        aws_access_key_id=creds.access_key_id,
        aws_secret_access_key=creds.secret_access_key,
    )
