# Log

## 2026-07-21

- Creation — [pipeline-architecture](/decisions/pipeline-architecture.md): 모노레포 구조,
  자기완결 처리 스크립트(PEP723+스크립트별 lock), Docker+pixi 시스템 환경 고정(최대
  durability·이미지 보존), pipeline/ 실행기(`pipeline/run.py`), geovars 단일 패키지,
  flat 스크립트 + git commit provenance 재현.
- Creation — geovars 패키지 스캐폴드 + 레이아웃 확정: `geovars/`가 `pyproject.toml` 소유,
  임포트 패키지는 `geovars/geovars/`(한 겹 중첩, src-layout 대신). optional extras 분리
  (catalog/pipeline/dashboard/modeling), 코어는 의존성 0·지연 임포트. 실행기는
  `pipeline/run.py`로 이동(실행은 pipeline/ 워크스페이스 책임), geovars 콘솔 명령은 폐기.
  → [pipeline-architecture](/decisions/pipeline-architecture.md) 구조·실행 섹션 갱신.
- Update — 기존 결정 기록을 grilling 재검토 결과에 맞게 정정:
  [knowledge-architecture](/decisions/knowledge-architecture.md)(정정 provenance는 자유 서술로,
  `[correction]` 마커 폐기), [reproducibility](/decisions/reproducibility.md)(코드 층·lock 강제
  재작성, `file:checksum`+R2 미러 명시), [versioning-and-corrections](/decisions/versioning-and-corrections.md)·
  [catalog-and-access](/decisions/catalog-and-access.md)·[governance-and-review](/decisions/governance-and-review.md)
  (`processing.py`→flat 스크립트·`stac-metadata/`·실행기 정합화).

## 2026-07-20

- Creation — OKF 번들 생성. `agent-native-refactoring` orphan 브랜치를 백지 씨앗으로 시작.
- Creation — [/principles.md](/principles.md): 세 가지 창립 원칙 기록.
- Creation — 의사결정 기록 7건 작성 (grilling 세션 결과):
  [knowledge-architecture](/decisions/knowledge-architecture.md),
  [versioning-and-corrections](/decisions/versioning-and-corrections.md),
  [reproducibility](/decisions/reproducibility.md),
  [catalog-and-access](/decisions/catalog-and-access.md),
  [governance-and-review](/decisions/governance-and-review.md),
  [knowledge-capture](/decisions/knowledge-capture.md),
  [infrastructure](/decisions/infrastructure.md).
