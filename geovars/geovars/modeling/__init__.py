"""geovars.modeling — 팀 변수생성·모델링 프로세스.

extra: [modeling]  (pip install "geovars[modeling]")

카탈로그의 collection 들을 입력으로 팀 내 변수를 생성하고 모델링하는 절차.
"""

from __future__ import annotations

try:
    import numpy  # noqa: F401
    import pandas  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.modeling 은 numpy·pandas 가 필요합니다: pip install "geovars[modeling]"'
    ) from exc

# TODO: 변수생성·모델링 파이프라인 구현.
