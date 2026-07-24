"""geovars — 연구팀 공간데이터 파이프라인·STAC 카탈로그 단일 패키지.

코어(CLI 부트스트랩)는 의존성 없이 얇게 유지한다. 무거운 기능은 각자의
optional extra로만 딸려오며, 코어에서 지연 임포트한다.

- geovars.pipeline   : [pipeline]  처리 스크립트용 유틸
- geovars.catalog    : [catalog]   STAC 카탈로그 로딩·검색 (pystac)
- geovars.dashboard  : [dashboard] marimo 기반 STAC 대시보드
- geovars.modeling   : [modeling]  팀 변수생성·모델링

세부 설계: .agents/skills/pipeline-script-shape/SKILL.md
"""

from __future__ import annotations

__version__ = "0.0.0"

# 지연 임포트 게이트: `geovars.catalog` 등을 접근하면 그때 임포트하고,
# extra 미설치로 실패하면 어떤 extra를 깔아야 하는지 명확히 알린다.
_FEATURE_MODULES = ("pipeline", "catalog", "dashboard", "modeling")


def __getattr__(name: str):
    if name in _FEATURE_MODULES:
        import importlib

        try:
            return importlib.import_module(f"{__name__}.{name}")
        except ImportError as exc:  # extra 미설치
            raise ImportError(
                f"geovars.{name} 를 쓰려면 해당 extra 를 설치하세요: "
                f'pip install "geovars[{name}]"'
            ) from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["__version__", *_FEATURE_MODULES]
