"""ardkr.storage — thin S3-compatible connection layer.

extra: [storage]  (pip install "ardkr[storage]")

Provides raw boto3 clients only. Path scheme, digests, upload conventions, and
STAC publishing belong to ``ardkr.pipeline``. A ``sign`` helper (presigned URLs)
may be added later.
"""

from __future__ import annotations

from enum import StrEnum

from ..common import S3Credentials, Secrets

try:
    import boto3
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.storage requires boto3: pip install "ardkr[storage]"'
    ) from exc


class Scope(StrEnum):
    """Object-store scope."""

    S3 = "s3"  # data bucket
    OPEN = "open"  # open bucket


def get_credentials(scope: Scope = Scope.S3) -> S3Credentials:
    """Return credentials for ``scope``.

    Args:
        scope: Bucket scope. Defaults to the data bucket.

    Returns:
        Credentials for that scope.
    """
    secrets = Secrets()
    if scope == Scope.S3:
        return secrets.s3
    return secrets.open


def get_client(scope: Scope = Scope.S3):
    """Return a boto3 S3 client for ``scope``.

    Args:
        scope: Bucket scope to connect to. Defaults to the data bucket.

    Returns:
        Configured boto3 S3 client.
    """
    creds = get_credentials(scope)
    return boto3.client(
        "s3",
        endpoint_url=creds.endpoint_url,
        aws_access_key_id=creds.access_key_id,
        aws_secret_access_key=creds.secret_access_key,
    )
