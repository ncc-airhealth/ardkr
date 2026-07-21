"""geovars.pipeline — 처리 스크립트용 공용 유틸.

extra: [pipeline]  (pip install "geovars[pipeline]")

처리 스크립트(pipeline/process/<collection-id>.py)가 소비하는 유틸. 스크립트는
geovars 를 git commit 으로 pin 해 옛 스크립트 재현성을 지킨다.
세부: knowledge/decisions/pipeline-architecture.md, reproducibility.md

담을 것(TODO):
- 원본 S3 호환 스토리지(현재 Cloudflare R2) 스냅샷 입력 로딩 + file:checksum(Multihash) 검증
- 처리 provenance(생성 git commit + image 버전) 기록
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 pystac 이 필요합니다: pip install "geovars[pipeline]"'
    ) from exc

try:
    import boto3
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 boto3 가 필요합니다: pip install "geovars[pipeline]"'
    ) from exc


# 캐시(pipeline/run.py 가 컨테이너에 마운트하는 `.cache/`)는 순수 가속 장치다 — 지워도
# 스크립트는 처음부터 다시 돌아 같은 결과를 내야 한다. 재현성은 3층 pin이 보장한다
# (knowledge/decisions/reproducibility.md). 여기 함수들은 그 캐시 경로를 읽기만 한다.


def cache_root() -> Path:
    """`.cache/`가 마운트된 위치(컨테이너 안에서는 보통 `/cache`)."""
    return Path(os.environ.get("GEOVARS_CACHE_ROOT", "/cache"))


def s3_cache_dir() -> Path:
    """S3 호환 오브젝트 스토리지(현재 Cloudflare R2)에서 받아온 객체의 로컬 read-through 미러 위치."""
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


def s3_cache_path(key: str) -> Path:
    """`.cache/s3/<key>` — 실제 S3 오브젝트 key 구조를 그대로 반영한 로컬 미러 경로.

    다운로드 read-through 미러와 업로드 전 스테이징 양쪽에 동일하게 쓰인다 — `.cache/s3/`가
    버킷의 로컬 거울이라는 하나의 개념으로 통일. 처리 스크립트는 이 경로에 직접 산출물을
    쓴 뒤 `upload_asset(key)`로 올린다.
    """
    path = s3_cache_dir() / key
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def upload_asset(key: str) -> str:
    """`.cache/s3/<key>`에 이미 만들어진 로컬 파일을 S3 호환 버킷(GEOVARS_S3_*)에 업로드하고
    file:checksum(Multihash)을 반환.

    같은 checksum을 객체 커스텀 메타데이터에도 넣어 HEAD 요청으로 1차 검증 가능하게 한다
    (knowledge/decisions/reproducibility.md 3층 pin의 "입력 collection 층").
    """
    data = s3_cache_path(key).read_bytes()
    checksum = multihash_sha256(data)
    client = boto3.client(
        "s3",
        endpoint_url=os.environ["GEOVARS_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["GEOVARS_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["GEOVARS_S3_SECRET_ACCESS_KEY"],
    )
    client.put_object(
        Bucket=os.environ["GEOVARS_S3_BUCKET_NAME"],
        Key=key,
        Body=data,
        Metadata={"checksum": checksum},
    )
    return checksum
