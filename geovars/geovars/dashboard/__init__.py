"""geovars.dashboard — marimo 기반 STAC 카탈로그 대시보드.

extra: [dashboard]  (pip install "geovars[dashboard]")

stac-metadata/ 카탈로그를 탐색·시각화하는 marimo 반응형 노트북/앱.
"""

from __future__ import annotations

try:
    import marimo  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.dashboard 는 marimo 가 필요합니다: pip install "geovars[dashboard]"'
    ) from exc

# TODO: marimo 앱 진입점(app()) 구현.
