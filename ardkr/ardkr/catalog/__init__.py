"""ardkr.catalog — STAC 카탈로그 로딩·검색.

extra: [catalog]  (pip install "ardkr[catalog]")

stac-metadata/ 의 파일 기반 STAC 카탈로그를 pystac 으로 로드하고, 상대경로를
해석해 collection/item 을 검색한다. 카탈로그 등록은 :func:`ardkr.storage.register_collection`.
"""

from __future__ import annotations

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.catalog 는 pystac 이 필요합니다: pip install "ardkr[catalog]"'
    ) from exc

# TODO: load_catalog() / search() 등 구현.
