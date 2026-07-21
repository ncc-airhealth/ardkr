---
type: decision
title: 파이프라인 아키텍처 — 처리 스크립트·환경·실행
description: 모노레포 구조, 자기완결 처리 스크립트(PEP723+lock), Docker+pixi로 시스템 환경 고정, Python 래퍼 실행, geovars 단일 패키지. 버전 재현은 flat 스크립트 + git commit provenance.
tags: [pipeline, monorepo, pixi, docker, pep723, uv, reproducibility, geovars]
timestamp: 2026-07-21
---

# 파이프라인 아키텍처 — 처리 스크립트·환경·실행

옛 refactoring-plan에서 딸려왔던(그러나 이 프로젝트에서 재합의된 적 없던) 처리
스크립트·의존성·Docker·공용 유틸 전반을 백지에서 다시 논의해 확정한 기록.

## 모노레포 구조

```
geovars/                       # geovars 컴포넌트 (자기완결)
  pyproject.toml               #   패키지 정의 + optional extras
  geovars/                     #   임포트 패키지 (대시보드·파이프라인 유틸·카탈로그 검색·모델링)
pipeline/                      # 처리 실행 워크스페이스
  run.py                       #   실행기: image 해석 → 컨테이너 → lock → uv run
  images/<YYYY.MM.DD>/         #   시스템 환경 정의: pixi.toml + pixi.lock + Dockerfile
  process/<collection-id>.py   #   flat 처리 스크립트 (+ <collection-id>.py.lock)
stac-metadata/                 # STAC JSON (데이터 사실의 SSOT). 버전 차원은 여기
knowledge/                     # OKF 지식
.claude/                       # 에이전트 skills
.gitignore  CLAUDE.md  README.md
```

- **컴포넌트 자기완결**: 각 최상위 디렉토리는 동급 컴포넌트다. Python 패키징 설정은
  레포 루트가 아니라 `geovars/`가 소유하고(`geovars/pyproject.toml`), 임포트 패키지는
  `geovars/geovars/`에 둔다(src-layout 대신 한 겹 중첩). 루트는 "레포=패키지"가 아니라
  모노레포다.
- **실행 소유권**: 처리 스크립트를 실행하는 책임은 `pipeline/` 워크스페이스에 있다.
  실행기는 `pipeline/run.py`이며, geovars 패키지의 콘솔 명령이 아니다.

## 처리 스크립트 모델

- **자기완결 단일 파일** — 스크립트마다 PEP 723 인라인 의존성 선언 + 스크립트별 lock,
  `uv run --script`로 실행. 옛 스크립트를 안 건드리고 새 스크립트에서 최신 라이브러리 채택
  가능. (기각한 대안: 단일 공용 환경 / editable 로컬 참조 — 후자는 옛 스크립트가 최신 유틸을
  써서 재현성 파괴)
- **flat 레이아웃** — `pipeline/process/<collection-id>.py`. **파일명 = collection id**.
- **버전 차원은 스크립트가 아니라 `stac-metadata/`에** 둔다. `pipeline/process/`는 flat =
  최신 스크립트만.
- **버전 재현은 git commit 기반** — 각 발행 버전의 **STAC provenance에 그 버전을 생성한
  git commit + `image` 버전을 기록**한다. 재현 = 그 commit을 checkout(→ 그때의 스크립트+lock)
  → 보존된 image pull → 실행.
  - 기각한 대안: 버전별 스크립트 디렉토리(`version=<v>/`). commit provenance가 어차피 필요
    하므로(유틸·image가 그 시점 것이어야 함) 스크립트 복사본은 중복. flat + commit이 더 단순.
  - 감수한 트레이드오프: HEAD에서 모든 버전 스크립트를 나란히 보는 편의를 포기하는 대신,
    단순성 + 재현 메커니즘 단일화(commit pin)를 택함.

## 시스템 환경 — Docker + pixi (최대 durability)

- 두 층이 분리된다: **Docker**(바깥, OS 층까지 고정) + **pixi**(안, conda-forge에서
  GDAL/GEOS/PROJ/uv를 `pixi.lock`으로 고정). "pixi로 만든 환경을 담은 Docker 컨테이너".
- **최대 durability를 위해 빌드된 이미지를 레지스트리에 보존**(냉동; 데이터 삭제금지 정책의
  이미지판) — 10년 후 재현은 "레시피 rebuild"가 아니라 "얼려둔 OCI 이미지 pull"이 가장 튼튼.
  빌드 정의(`Dockerfile` + `pixi.lock`)도 레포에 커밋해 rebuild도 가능하게 둔다.
- **`pipeline/images/<YYYY.MM.DD>/`** = `pixi.toml` + `pixi.lock` + `Dockerfile` (빌드 정의).
  식별자는 `YYYY.MM.DD` (같은 날 두 번 갱신 시 `-2` 접미사).
- **스크립트가 자기 시스템 환경을 pin** — PEP 723 블록 안 커스텀 테이블에:

  ```python
  # /// script
  # dependencies = ["duckdb", "pyproj"]
  #
  # [tool.geovars]
  # image = "2026.07.20"        # → pipeline/images/2026.07.20/
  # ///
  ```

  시스템 deps를 올리면 새 `images/<날짜>/`를 만들고, 옛 스크립트는 계속 옛 `image`를 가리킴
  ([/decisions/reproducibility.md](/decisions/reproducibility.md)의 시스템 층 pin).
- **단일 정규 arch `linux/amd64`** — 한 arch = 결정론적 출력. Mac(arm64)에선 에뮬레이션으로
  실행(느리지만 결과는 정규 arch로 통일). 대량 처리 속도가 문제되면 그때 재검토.
  (기각: multi-arch — cross-arch 부동소수점/SIMD 출력 차이 위험. plain Dockerfile+apt —
  apt 미러가 옛 버전을 지워 rebuild 불가. pixi-only — OS 층 미고정 + pixi 신생 도구 리스크.)

## 실행 — pipeline/ 워크스페이스의 실행기 (크로스플랫폼)

- 처리 스크립트 실행은 **`pipeline/` 워크스페이스의 책임**이다. 실행기 `pipeline/run.py`
  (Python, stdlib 부트스트랩)로 Windows·Mac·Linux에서 동일 실행. (`.sh`는 Windows 네이티브
  불가라 기각. geovars 패키지의 콘솔 명령으로 두는 방식도 기각 — 실행은 파이프라인 관심사지
  라이브러리 관심사가 아니다.) 컨테이너 없이도 도는 얇은 부트스트랩으로 chicken-egg 회피.
- 실행기 한 번 실행: ① 스크립트 상단 `image` 읽기 → 그 컨테이너 진입 → ② lock 처리 →
  ③ `uv run --script`.
- **lock 동작 규칙**: **없으면 컨테이너 안에서 생성 / 있으면 frozen 그대로 사용 / 재-lock은
  명시적 플래그로만**(`--relock`). 매 실행 자동 재생성 금지(pin 무효화 방지). 재-lock은
  의존성을 의도적으로 바꾸는 것이므로, 산출물이 발행됐다면 **새 버전으로 취급**.
- **lock 커밋은 필수**(규칙). **CI는 도입하지 않기로 확정** — 커밋 여부를 확인하는 자동
  게이트는 없다. 위반은 사후 발견에 의존한다
  ([/decisions/reproducibility.md](/decisions/reproducibility.md)).

## 공용 유틸 — geovars 단일 패키지

- 스크립트는 공용 유틸을 **버전 고정으로 소비**해야 옛 스크립트 재현성이 안 깨진다.
  → PEP 723에서 `geovars`를 **git commit으로 pin**(예: `geovars @ git+<repo>@<commit>`).
  운영이 안정되면 semver **git 태그**로 전환.
- `geovars`는 **단일 패키지 + optional extras 엄격 분리**: marimo 기반 STAC 대시보드,
  파이프라인 유틸, STAC 카탈로그 검색, 팀 변수생성·모델링. 코어는 지연 임포트, 각 기능은
  자기 extra만 — 스크립트가 `geovars[pipeline]`을 끌 때 대시보드·모델링 deps가 안 딸려오게.
  (분리가 실제로 아프면 그때 안정 코어를 별 패키지로 떼어냄.)

## 미해결

- 실행기(`pipeline/run.py`)의 진입 방식·인자. (현재 경로/`image`/lock 판정 로직만 구현.
  컨테이너 진입·`uv`/`docker` 연동과 CLI 진입점은 미구현.) 정확한 CLI 계약은 실행기를
  실제로 구현할 때 정하고 `capture-knowledge`로 사후 반영한다.
- 이미지 레지스트리 선택(GHCR / R2 등)과 보존 운영.
- provenance schema(이미지 digest·lock·입출력 manifest)의 정확한 필드명, R2 업로드·STAC
  발행의 staging·복구 절차, 재현 원커맨드 — 구현 시점에 정하고 사후 포착.

CI는 도입하지 않기로 확정했으므로
([/decisions/reproducibility.md](/decisions/reproducibility.md)), lock 커밋·catalog
정합성 등의 자동 게이트는 이 목록에서 제외한다 — 미해결이 아니라 **안 하기로 결정**됐다.

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
