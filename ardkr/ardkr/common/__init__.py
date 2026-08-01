"""ardkr.common — shared package utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class S3Credentials:
    """Credentials for one S3-compatible storage scope."""

    bucket_name: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str


class Secrets:
    """S3 credentials for the data and open buckets, read from the environment."""

    def __init__(self) -> None:
        self.s3 = S3Credentials(
            bucket_name=os.environ["ARDKR_S3_BUCKET_NAME"],
            endpoint_url=os.environ["ARDKR_S3_ENDPOINT_URL"],
            access_key_id=os.environ["ARDKR_S3_ACCESS_KEY_ID"],
            secret_access_key=os.environ["ARDKR_S3_SECRET_ACCESS_KEY"],
        )
        self.open = S3Credentials(
            bucket_name=os.environ["ARDKR_OPEN_S3_BUCKET_NAME"],
            endpoint_url=os.environ["ARDKR_OPEN_S3_ENDPOINT_URL"],
            access_key_id=os.environ["ARDKR_OPEN_S3_ACCESS_KEY_ID"],
            secret_access_key=os.environ["ARDKR_OPEN_S3_SECRET_ACCESS_KEY"],
        )
