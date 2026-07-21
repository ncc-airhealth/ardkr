"""geovars.pipeline — 처리 스크립트용 공용 유틸.

extra: [pipeline]  (pip install "geovars[pipeline]")

처리 스크립트(pipeline/process/<collection-id>.py)가 소비하는 유틸. 스크립트는
geovars 를 git commit 으로 pin 해 옛 스크립트 재현성을 지킨다.
세부: knowledge/decisions/pipeline-architecture.md, reproducibility.md

담을 것(TODO):
- 원본 R2 스냅샷 입력 로딩 + file:checksum(Multihash) 검증
- STAC Item/Collection 생성 헬퍼(pystac) → stac-metadata/ 로 기록
- 처리 provenance(생성 git commit + image 버전) 기록
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 pystac 이 필요합니다: pip install "geovars[pipeline]"'
    ) from exc


# 캐시(pipeline/run.py 가 컨테이너에 마운트하는 `.cache/`)는 순수 가속 장치다 — 지워도
# 스크립트는 처음부터 다시 돌아 같은 결과를 내야 한다. 재현성은 3층 pin이 보장한다
# (knowledge/decisions/reproducibility.md). 여기 함수들은 그 캐시 경로를 읽기만 한다.


def cache_root() -> Path:
    """`.cache/`가 마운트된 위치(컨테이너 안에서는 보통 `/cache`)."""
    return Path(os.environ.get("GEOVARS_CACHE_ROOT", "/cache"))


def r2_cache_dir() -> Path:
    """R2에서 받아온 객체의 로컬 read-through 미러 위치."""
    return Path(os.environ.get("GEOVARS_R2_CACHE_DIR", str(cache_root() / "r2")))


def duckdb_cache_dir() -> Path:
    """duckdb extension·spill(temp_directory) 위치."""
    return Path(os.environ.get("GEOVARS_DUCKDB_CACHE_DIR", str(cache_root() / "duckdb")))


def scratch_dir() -> Path:
    """현재 처리 스크립트(collection)의 중간산출물 스크래치 디렉토리."""
    return Path(os.environ.get("GEOVARS_SCRATCH_DIR", str(cache_root() / "pipeline")))
