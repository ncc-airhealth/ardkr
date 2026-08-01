"""ardkr.common — shared package utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class S3Credentials:
    """Credentials for one S3-compatible logical store."""

    bucket_name: str
    endpoint_url: str
    access_key_id: str
    secret_access_key: str


class Secrets:
    """Private and open store credentials from the environment."""

    def __init__(self) -> None:
        self.private = S3Credentials(
            bucket_name=os.environ["ARDKR_PRIVATE_BUCKET_NAME"],
            endpoint_url=os.environ["ARDKR_PRIVATE_ENDPOINT_URL"],
            access_key_id=os.environ["ARDKR_PRIVATE_ACCESS_KEY_ID"],
            secret_access_key=os.environ["ARDKR_PRIVATE_SECRET_ACCESS_KEY"],
        )
        self.open = S3Credentials(
            bucket_name=os.environ["ARDKR_OPEN_BUCKET_NAME"],
            endpoint_url=os.environ["ARDKR_OPEN_ENDPOINT_URL"],
            access_key_id=os.environ["ARDKR_OPEN_ACCESS_KEY_ID"],
            secret_access_key=os.environ["ARDKR_OPEN_SECRET_ACCESS_KEY"],
        )
