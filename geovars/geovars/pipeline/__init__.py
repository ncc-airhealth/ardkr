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

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.pipeline 은 pystac 이 필요합니다: pip install "geovars[pipeline]"'
    ) from exc
