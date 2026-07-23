"""geovars.pipeline — 처리 스크립트용 공용 유틸.

extra: [pipeline]  (pip install "geovars[pipeline]")

처리 스크립트(pipeline/process/<collection-id>.py)가 소비하는 유틸. 스크립트는
geovars 를 git commit 으로 pin 해 옛 스크립트 재현성을 지킨다.
세부: knowledge/decisions/pipeline-architecture.md, reproducibility.md,
secrets-and-s3-client.md

담을 것(TODO):
- 원본 S3 호환 스토리지(현재 Cloudflare R2) 스냅샷 입력 로딩 + file:checksum(Multihash) 검증
- 처리 provenance(생성 git commit + image 버전) 기록
"""

from __future__ import annotations

import hashlib
import io
import os
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

try:
    import pystac
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 pystac 이 필요합니다: pip install "geovars[pipeline]"'
    ) from exc

try:
    from cloudpathlib import S3Client, S3Path
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 cloudpathlib[s3] 이 필요합니다: pip install "geovars[pipeline]"'
    ) from exc

try:
    from botocore.exceptions import ClientError
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 botocore 가 필요합니다: pip install "geovars[pipeline]"'
    ) from exc

from pystac.extensions.file import FileExtension


# 캐시(pipeline/run.py 가 컨테이너에 마운트하는 `.cache/`)는 순수 가속 장치다 — 지워도
# 스크립트는 처음부터 다시 돌아 같은 결과를 내야 한다. 재현성은 3층 pin이 보장한다
# (knowledge/decisions/reproducibility.md). 여기 함수들은 그 캐시 경로를 읽기만 한다.


def cache_root() -> Path:
    """`.cache/`가 마운트된 위치(컨테이너 안에서는 보통 `/cache`)."""
    return Path(os.environ.get("GEOVARS_CACHE_ROOT", "/cache"))


def s3_cache_dir() -> Path:
    """S3 호환 오브젝트 스토리지(현재 Cloudflare R2)의 로컬 read-through 미러 위치.

    `s3_client()`의 `local_cache_dir`로 그대로 넘어간다 — 실제 파일 경로는
    cloudpathlib 관례(`<이 경로>/<bucket>/<key>`)를 따른다.
    """
    return Path(os.environ.get("GEOVARS_S3_CACHE_DIR", str(cache_root() / "s3")))


def duckdb_cache_dir() -> Path:
    """duckdb extension·spill(temp_directory) 위치."""
    return Path(os.environ.get("GEOVARS_DUCKDB_CACHE_DIR", str(cache_root() / "duckdb")))


def scratch_dir() -> Path:
    """현재 처리 스크립트(collection)의 중간산출물 스크래치 디렉토리."""
    return Path(os.environ.get("GEOVARS_SCRATCH_DIR", str(cache_root() / "pipeline")))


def multihash_sha256(data: bytes) -> str:
    """STAC File Info extension의 `file:checksum` 형식(Multihash, sha2-256)으로 인코딩.

    Multihash = <함수코드><다이제스트 길이><다이제스트>, sha2-256은 0x12/0x20 →
    16진 접두 "1220" + sha256 hex digest.
    """
    return "1220" + hashlib.sha256(data).hexdigest()


def s3_client() -> S3Client:
    """GEOVARS_S3_* 환경변수로 인증하고 `s3_cache_dir()`를 로컬 read-through 캐시로 쓰는 클라이언트.

    호출마다 새로 만든다 — 캐시는 client 인스턴스가 아니라 디스크(local_cache_dir)에 있으므로
    재사용해도 얻는 게 없다.
    """
    return S3Client(
        endpoint_url=os.environ["GEOVARS_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["GEOVARS_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["GEOVARS_S3_SECRET_ACCESS_KEY"],
        local_cache_dir=s3_cache_dir(),
    )


def s3_path(key: str) -> S3Path:
    """`s3://<GEOVARS_S3_BUCKET_NAME>/<key>` — 로컬 read-through 캐시가 붙은 cloudpathlib 경로.

    다운로드는 이 객체의 `.open()`/`.read_bytes()`/`.download_to()`를 그대로 쓴다 — 필요한 것만
    받아오는 캐시 판단은 cloudpathlib이 로컬/클라우드 mtime을 비교해 알아서 한다.
    """
    bucket = os.environ["GEOVARS_S3_BUCKET_NAME"]
    return S3Path(f"s3://{bucket}/{key}", client=s3_client())


def remote_checksum(key: str) -> str | None:
    """R2 객체의 커스텀 메타데이터 `checksum`을 HEAD 요청만으로 읽는다(본문 다운로드 없음).

    객체가 없으면 None. `publish_asset(mode="remote")`의 재업로드 스킵 판단과, 처리
    스크립트의 `verify_uploaded` 단계가 공유하는 헬퍼다.
    """
    path = s3_path(key)
    try:
        obj = path.client.s3.Object(path.bucket, path.key)
        return obj.metadata.get("checksum")  # .metadata 접근이 HEAD(load)를 트리거
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return None
        raise


def publish_asset(
    asset: pystac.Asset,
    key: str,
    write: Callable[[BinaryIO], None],
    mode: str = "remote",
) -> str:
    """`write(파일객체)`로 내용을 채워 발행하고, `asset`에 checksum까지 기록한다.

    `asset`은 호출 전에 이미 `item.add_asset(...)`로 owner가 있는 상태여야 한다 —
    `FileExtension.ext(asset, add_if_missing=True)`가 owner 없는 Asset에는 스키마 URI를
    등록할 곳이 없어 실패한다.

    `write()`를 먼저 메모리 버퍼에 실행해 checksum을 계산한 뒤 `mode`에 따라 분기한다.

    - `mode="remote"`(기본): 원격에 같은 checksum이 이미 있으면(`remote_checksum`) 업로드를
      생략하고, 아니면 R2에 올린 뒤 checksum을 서버사이드 메타데이터(`copy_from` — 네트워크
      재전송 없음)로 반영한다.
    - `mode="local"`: R2를 건드리지 않고 로컬 캐시(`.cache/s3/<bucket>/<key>`)에만 쓴다.
      빠른 개발 반복용이며, 이 상태로 발행됐다고 볼 수 없다 — 처리 스크립트의
      `verify_uploaded`가 이후 반드시 실패한다.

    어느 mode든 asset의 `file:checksum`은 기록되고 checksum이 반환된다. 커스텀 메타데이터는
    HEAD 요청만으로 하는 1차 검증용이고, 권위 있는 검증은 항상 실제 바이트 해시다
    (knowledge/decisions/reproducibility.md 3층 pin의 "입력 collection 층").
    """
    buffer = io.BytesIO()
    write(buffer)
    data = buffer.getvalue()
    checksum = multihash_sha256(data)

    if mode == "local":
        cache_file = s3_cache_dir() / os.environ["GEOVARS_S3_BUCKET_NAME"] / key
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(data)
    elif mode == "remote":
        if remote_checksum(key) != checksum:
            path = s3_path(key)
            with path.open("wb") as f:
                f.write(data)
            path.client.s3.Object(path.bucket, path.key).copy_from(
                CopySource={"Bucket": path.bucket, "Key": path.key},
                Metadata={"checksum": checksum},
                MetadataDirective="REPLACE",
            )
        # else: 원격에 같은 checksum이 이미 있음 → 업로드 생략
    else:
        raise ValueError(f"알 수 없는 publish mode: {mode!r} (local|remote)")

    FileExtension.ext(asset, add_if_missing=True).checksum = checksum
    return checksum
