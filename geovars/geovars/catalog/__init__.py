"""geovars.catalog — STAC 카탈로그 로딩·검색.

extra: [catalog]  (pip install "geovars[catalog]")

stac-metadata/ 의 파일 기반 STAC 카탈로그를 pystac 으로 로드하고, 상대경로를
해석해 collection/item 을 검색한다. 카탈로그 갱신은 load-mutate-save 방식.
세부: knowledge/decisions/catalog-and-access.md
"""

from __future__ import annotations

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.catalog 는 pystac 이 필요합니다: pip install "geovars[catalog]"'
    ) from exc

# TODO: load_catalog() / search() / latest_version() 등 구현.
